from PIL import Image,ImageDraw,ImageFont
import math,os,PIL,random,time

class DniNumbers:
    def __init__(self,**kwargs):
        self.bg       = self.set_bg(kwargs.get("bg_image",None))
        self.color    = kwargs.get("color",(20,20,20))
        self.bg_color = kwargs.get("bg_color",self.color)
        self.fg_color = kwargs.get("fg_color",self.color)
        self.box_size = kwargs.get("box_size",100)
        self.show_num = kwargs.get("show_num",False)

    def set_bg(self,bg_image=None):
        if isinstance(bg_image,str) and os.path.exists(bg_image):
            # Try to load it
            try:
                self.bg = Image.open(bg_image).convert("RGBA")
            except: # Failed to load - clear it
                self.bg = None
        elif isinstance(bg_image,PIL.Image.Image):
            # Already an image file - make sure it supports transparency
            self.bg = bg_image.convert("RGBA")
        else:
            # Not sure what type this is - let's just clear it as a failsafe
            self.bg = None
        return self.bg

    def to_b25(self,n):
        chars = "0123456789abcdefghijklmno" # Representations of each char for the base-25 numbers
        n = int(n)
        digits = ""
        while n:
            digits = chars[int(n%25)] + digits
            n //= 25
        return digits if len(digits) else "0" # Assume 0 if we get nothing

    def to_b10(self,n):
        return int(str(n),25)

    def draw_0(self,d,x,y,w,h,line_w,color):
        # Draws the dot in the center of the passed box representing 0
        # Find the center
        l = line_w/4
        c_x,c_y = w/2+x, h/2+y
        # Draw the dot as a circle
        d.ellipse([(c_x-l,c_y-l),(c_x+l,c_y+l)],fill=color)

    def draw_1(self,d,x,y,w,h,line_w,color,rotated=False):
        # Draws the center line representing 1
        # Get the center of X
        l = int(line_w/2)
        x1 = w/2+x
        y1 = h/2+y
        if rotated:
            # Draw a horizontal line
            d.line([(x,y1),(x+w,y1)],fill=color,width=l)
        else:
            # Draw a vertical line
            d.line([(x1,y),(x1,y+h)],fill=color,width=l)

    def draw_2(self,d,x,y,w,h,line_w,color,rotated=False):
        # Draws the arc representing 2 - takes up 1/4 of the box
        l = int(line_w/2)
        x1 = w/4+x
        y1 = h/4*3+y
        if rotated:
            # Draw it horizontally on the bottom
            d.arc([(x-line_w,y1),(x+w+line_w,y+h+h/4*3)],165,15,color,width=l)
        else:
            # Draw it vertically on the left
            d.arc([x-(w/4*3),y-line_w,x1,y+h+line_w],-75,75,color,width=l)

    def draw_3(self,d,x,y,w,h,line_w,color,rotated=False):
        # Draws the 2 converging lines representing 3 - takes half the box
        l = int(line_w/2)
        x1 = w/2+x
        y1 = h/2+y
        if rotated:
            # Draw it pointing down
            d.line([(x-l,y1),(x1,y+h+l)],fill=color,width=l)
            d.line([(x1,y+h+l),(x+w+l,y1)],fill=color,width=l)
        else:
            # Draw it pointing left
            d.line([(x1,y-l),(x-l,y1)],fill=color,width=l)
            d.line([(x-l,y1),(x1,y+h+l)],fill=color,width=l)
        
    def draw_4(self,d,x,y,w,h,line_w,color,rotated=False):
        # Draws the hitched lines representing 4
        l = int(line_w/2)
        if rotated:
            # Draw the hitch on the left going up
            x1 = w/4+x
            y1 = h/2+y
            d.line([(x1,y),(x1,y1+int(l/2))],fill=color,width=l)
            d.line([(x1,y1),(x+w,y1)],fill=color,width=l)
        else:
            # Draw the hitch on the top going right
            x1 = w/2+x
            y1 = h/4+y
            d.line([(x1-int(l/2),y1),(x+w,y1)],fill=color,width=l)
            d.line([(x1,y1),(x1,y+h)],fill=color,width=l)

    def draw_cap(self,d,x,y,l,color):
        l1 = int(l/2)-1
        if l1 < 1:
            return # Nothing to draw here - don't even waste time
        d.ellipse([(x-l1,y-l1),(x+l1,y+l1)],fill=color)

    def crop(self,image,w,h):
        new_image = image
        # Grow the image if need be, then crop
        grow = max(w/image.width,h/image.height)
        image = image if grow <= 1 else image.resize((int(math.ceil(image.width*grow)),int(math.ceil(image.height*grow))),resample=PIL.Image.LANCZOS)
        x,y = random.randint(0,image.width-w),random.randint(0,image.height-h)
        return image.crop((x,y,x+w,y+h))

    def draw_icon(self,number):
        # Let's first get some information from our box size
        bs = self.box_size * 2 # Draw at double res so we can shrink to "antialias"
        outer_line_width = int(bs/10) # Box size is the internal dimensions of the box
        # The symbols will have an overhang to the left and right of both the top and bottom
        # lines on the first and last boxes - so they'll be a full width of box_size * num_boxes + outer_line_width * 2
        assert len(str(number)) <= 100, "Input number is over 100 characters!  Will consume too many resources to draw!"
        chars = self.to_b25(number)
        image_w = int(math.ceil(bs * len(chars) + outer_line_width * (len(chars) + 3)))
        image_h = int(math.ceil(bs + outer_line_width * 2))
        # First, let's draw the outline and separators
        im = Image.new("RGBA",(image_w,image_h),(0,0,0,0))
        d  = ImageDraw.Draw(im)
        # Let's walk the characters, and draw each value
        for y,x in enumerate(chars):
            # Determine which we need to draw
            i = self.to_b10(x)
            base = i//5
            sub  = i-base*5
            # Get the box's coordinates
            x1 = y*bs + (y+2)*outer_line_width
            y1 = outer_line_width
            # Save the functions in a list - will be called by index
            func_list = [self.draw_0,self.draw_1,self.draw_2,self.draw_3,self.draw_4]
            if base == sub == 0:
                func_list[0](d,x1,y1,bs,bs,outer_line_width,self.fg_color)
            if base:
                func_list[base](d,x1,y1,bs,bs,outer_line_width,self.bg_color,True)
            if sub:
                func_list[sub](d,x1,y1,bs,bs,outer_line_width,self.fg_color)
        pad_width = outer_line_width/2 # Allows us to draw rounded caps to our lines
        # Top:  x1,y1 -> x2,y1    Then Bottom: x1,y2 -> x2,y2
        d.line([(pad_width,pad_width),(image_w-pad_width,pad_width)],fill=self.color,width=outer_line_width)
        d.line([(pad_width,image_h-pad_width),(image_w-pad_width,image_h-pad_width)],fill=self.color,width=outer_line_width)
        # Draw the circle caps, top left, top right, bottom left, bottom right
        self.draw_cap(d,pad_width,pad_width,outer_line_width,self.color)
        self.draw_cap(d,image_w-pad_width,pad_width,outer_line_width,self.color)
        self.draw_cap(d,pad_width,image_h-pad_width,outer_line_width,self.color)
        self.draw_cap(d,image_w-pad_width,image_h-pad_width,outer_line_width,self.color)
        # Start walking the number of boxes and draw the separator lines
        for x in range(len(chars)+1):
            # Get the start of the x location
            x1 = x*bs + (x+1)*outer_line_width + pad_width
            d.line([(x1,pad_width),(x1,image_h-pad_width)],fill=self.color,width=outer_line_width)
        # Check if we have a bg_image - and try to load it
        pad = int(image_h/3)
        b = self.bg if self.bg else Image.new("RGBA",(image_w+pad*2,image_h+pad*2),(0,0,0,0)) # create a blank canvas if no bg image
        # Resize the bg image
        pad = int(image_h/3)
        bg = self.crop(b,image_w+pad*2,image_h+pad*2)
        im = im.convert("RGBA")
        bg.paste(im,(pad,pad),mask=im)
        # Write the numeric value on the image if needed
        if self.show_num:
            d = ImageDraw.Draw(bg)
            d.text((pad,image_h+int(pad*1.15)),"{:,}".format(int(number)),self.color,font=ImageFont.truetype("OpenSans-Semibold.ttf",outer_line_width*2))
        return bg.resize((int(bg.width/2),int(bg.height/2)),resample=PIL.Image.LANCZOS)

os.chdir(os.path.dirname(os.path.realpath(__file__)))
d = DniNumbers(box_size=100,show_num=True,bg_image="paper.png")#,color=(20,20,20),bg_color=(70,70,70),fg_color=(120,120,120))
while True:
    n = input("Choose a number (or q to quit):  ")
    if n.lower() in ["q","quit","exit"]:
        exit()
    t = time.time()
    i = d.draw_icon(n)
    i.save("{}.png".format("torture" if len(n) == 2000 else n),"PNG")
    print(" - Saved to {}.png!".format("torture" if len(n) == 2000 else n))
    print(" --> Took {} seconds.".format(time.time()-t))
import sys,os

from PIL import Image,  ImageOps

mask_rgb_threshold=220

def is_close_to_white(pixel, threshold):
    return all(value > threshold for value in pixel)

#this distorts colors too much
def convert_to_white_CONTRAST(image_path, threshold):
    with Image.open(image_path) as img:
        img=ImageOps.autocontrast(img, cutoff = 2, ignore = 2)
        new_path=image_path.replace('.png','_new.png')
        img.save(new_path)

def convert_to_white(image_path, threshold):
    rng=[170,190,200,210,230]
    #I would like to pick the highest one which at least is a big drop from its successor
    #i.e. for "number of pixels changed"
    #TODO finish this.
    return convert_to_white_INNER(image_path, threshold)


#this should really iterate around the threshold looking for a good spot to "mega-convert" cause randomly picking X is wrong.
def convert_to_white_INNER(image_path, threshold):
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        pixels = img.load()
        changed=0
        for i in range(img.width):
            for j in range(img.height):
                if is_close_to_white(pixels[i, j], threshold):
                    pixels[i, j] = (255, 255, 255)
                    changed+=1

        new_path=image_path.replace('.png','_new.png')
        img.save(new_path)



#issue with actual prints (on an epson 8550): although each card is clearly supposed to be 3 2/3 inch long (11/3), the first card IS that long approx. The 2nd is NOT, it's too long, and the third is too short.  Is there somehow a slipping of the gears or something? it's insane.
#result: yes, my printer "thinks" the paper is longer than it is, or, is disproportionally shrinking/zooming the image in even under the strictest conditions.

#.  Solution: artificially crush the image down by adding fake whitespace to the left (a bit) and right (a lottish) so that the actual projection of the image on the actual paper is now borderless.

raw_length=3300
raw_width=2550
ratio=11/8.5
#some images will come in tall and skinny, others square, others "wide". I should expand them so they have enough whitespace on the side so the ratio is good, (or warn if too "fat" wide).  That way 1s, 2s will be normalized.
#then shrink them to the right size, then normal layout.  3x3 is good.

#adjustment 2: many images may have a non-pure-white background. how can I grab that and convert it to something sane so that when I expand the card, the background isn't bad?

#adjustment 3:   many images may not use the full width. just position them in the middle of the region and leave whitespace around them.  problem: the background is defined to be grey (for the line-leftover purpose)
#solution: expand the image to its apparent full size by pasting it into the middle.

#normal playing card size, laid out in 3x3 lengthwise on a landscape image.
#big_image_size=(1050, 750)
big_grid_size=(3, 3) #this is 9 sheets in total for a set.
big_image_size=(int(raw_length/(big_grid_size[0]*1.0)), int(raw_width/(big_grid_size[1]*1.0)))


#falsely small cards
#small_image_size=(630, 450)
#small_grid_size=(5, 5) #not bad, 4 sheets in total, but a lot of waste, primarily in the last sheet which only has 6 cards in it.

#dpi size of an 8.5x11 sheet of paper:
# 3300x2550
# 22x17
# 44x34
# 88x68
# 176x136
# 352x272
# 704x522

#this is the background color of the main image. we position cards in it after shrinking the non-right-bottom edge cards by one pixel in their non-"edge" direction.
guide_color_unit=150
guideline_color=(guide_color_unit,guide_color_unit,guide_color_unit)

# Function to create a 3x3 grid image
def create_grid(orig_image_fps, grid_size, image_size):
    # Create a new blank image with the size of the entire grid
    print("making grid with image_size: ",image_size)
    grid_image = Image.new("RGB", (grid_size[0] * image_size[0], grid_size[1] * image_size[1]), guideline_color)
    for ii in range(grid_size[0]):
        for jj in range(grid_size[1]):
            # Open the image corresponding to the current grid position
            fp=orig_image_fps[ii * grid_size[1] + jj]
            if not os.path.exists(fp):
                print("bad path:",fp)
                sys.exit()
            img = Image.open(fp)
            width, height = img.size
            print(fp)


            #now we paste the image into a new wider image of the appropriate size.
            if (img.size[0]<image_size[0]):
                #image may be too tall, shrink it vertically.
                if (img.size[1]>image_size[1]):
                    target=(int(img.size[0]*image_size[1]/img.size[1]), int(image_size[1]))
                    img=img.resize(target)

                print("enwidening.")
                blankim=Image.new("RGB", image_size, (255,255,255))
                paste_x=int((image_size[0]-img.size[0])/2) #how pushed in it is.
                blankim.paste(img, (paste_x,0))
                img=blankim

            #some magic here. if we are not the LAST image, then shrink the image by 1 pixel xy wise so that
            #the light grey background shows through, so we can cut the image easily.
            #but do not shrink the rightmost or bottommost images.
            using_size=(image_size[0]-1, image_size[1]-1)
            if ii==2:
                using_size=(image_size[0], using_size[1])
            if jj==2:
                using_size=(using_size[0], image_size[1])

            print(img.size, 'resizing to:', using_size)
            img = img.resize(using_size)

            # Paste the image into the correct position in the grid based on IMAGE_SIZE which is global, absolute, correct.
            #it just so happens that in non-bottom, non-right side cases the image will be shrunk.
            targetxy=(ii * image_size[0], jj * image_size[1])
            print("pasting at",targetxy,'in global.')
            grid_image.paste(img, targetxy)
            #grid_image.save("%d-%d.png"%(ii,jj))

    return grid_image



# Function to create a 3x3 grid image
def prepare_images(to_fix_image_fps):
    for fp in to_fix_image_fps:
        if not os.path.exists(fp):
            print("bad path:",fp)
            sys.exit()
        convert_to_white(fp, mask_rgb_threshold)

folders=['stripe','letter','watercolor',]
subfolders=['a','b','c',]
base_path='/mnt/d/proj/set-making/first-set-making/second/'

folders=['stipple',]
for folder in folders:
    for subf in subfolders:
        print(folder,subf)
        path=base_path+folder+'/'+subf
        # List of image paths
        to_fix_image_fps= sorted([path+'/'+f for f in os.listdir(path) if '_new.png' not in f][:9])
        prepare_images(to_fix_image_fps )
        print("images prepared.")
        orig_image_fps= sorted([path+'/'+f for f in os.listdir(path) if '_new.png' in f][:9])

        if len(orig_image_fps)<9: continue

        # Create the grid image
        grid = create_grid(orig_image_fps, big_grid_size, big_image_size)

        force_extra_whitespace_right=1/73.0*raw_length
        force_extra_whitespace_left=int(force_extra_whitespace_right/4.2)

        print("force right=",force_extra_whitespace_right)
        print("force left=",force_extra_whitespace_left)

        #my printer "magically" adds approximately 1/24th inch "stretching" to the first two images, so that the last image is down in size by that much (since it overprints the edge on the bottom/longest part of the page).
        #here I attempt to compensate for that by remapping the existing pixel-perfect image into one which is slightly shrunken on the X (long page) axis.
        grid_image2 = Image.new("RGB", (grid.size[0], grid.size[1]), (255,255,255))
        target_size=(int(grid.size[0]-force_extra_whitespace_left-force_extra_whitespace_right), int(grid.size[1]))
        gg=grid.resize(target_size)
        grid_image2.paste(gg, (force_extra_whitespace_left,0))

        # Save or display the grid image
        output='%s_%s_1.png'%(folder, subf)
        grid_image2.save(output)
        print("saved to: ",output)

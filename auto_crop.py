import cv2
import os
import glob
import time
import zipfile

def get_contours(img, fname=None, debug=False):
    # First make the image 1-bit and get contours
    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(imgray, 15,255,cv2.THRESH_BINARY)
    if fname:
        threshname = 'cropped/' + os.path.basename(fname) + '_thresh.png'
    else:
        threshname = 'thresh.jpg'
        
    b, g, r = cv2.split(img)
    rgba = [b,g,r, thresh]
    dst = cv2.merge(rgba,4)
    
    if debug: cv2.imwrite(threshname, dst)
    
    contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

    ih, iw = get_size(img)
    contours = [cc for cc in contours if contourOK(cc, ih, iw)]
    
    return contours
    
def get_size(img):
    ih, iw = img.shape[:2]
    return ih, iw
    
def contourOK(cc, ih, iw):
    x, y, w, h = cv2.boundingRect(cc)
    return (w*h)/(iw*ih)

def find_boundaries(fname, img, contours):
    # margin is the minimum distance from the edges of the image, as a fraction
    ih, iw = img.shape[:2]
    minx = iw
    miny = ih
    maxx = 0
    maxy = 0
    for cc in contours:
        x, y, w, h = cv2.boundingRect(cc)
        # get absolute max and min values
        if x < minx: minx = x
        if y < miny: miny = y
        if x + w > maxx: maxx = x + w
        if y + h > maxy: maxy = y + h
    return (minx, miny, maxx, maxy)

def crop(img, boundaries):
    minx, miny, maxx, maxy = boundaries
    return img[miny:maxy, minx:maxx]

def process_image(fname, cnt, base_dir, pg_sigfigs, debug):
    img = cv2.imread(fname)
    contours = get_contours(img, fname, debug)
    bounds = find_boundaries(fname, img, contours)
    cropped = crop(img, bounds)
    pg_format_str = 'page{:0'+str(pg_sigfigs)+'d}.jpg'
    proc_filename = os.path.join(base_dir, 'cropped', pg_format_str.format(cnt))
    cv2.imwrite(proc_filename, cropped)
    return proc_filename

def zipdir(files, f_zip, base_dir):
    # ziph is zipfile handle
    ziph = zipfile.ZipFile(os.path.join(base_dir, f_zip+'.cbz'), 'w', zipfile.ZIP_DEFLATED)
    for file in sorted(files):
        ziph.write(file)
    ziph.close()

def find_images_and_process(output, base_dir=os.getcwd(), debug=False):
    print(output)
    print(base_dir)
    # check for cropped
    if not os.path.isdir(os.path.join(base_dir,output,'cropped')):
        os.mkdir(os.path.join(base_dir,output,'cropped'))
    # set counter
    cnt = 1
    files = []
    tot_files = len(glob.glob(os.path.join(base_dir,output,'*.jpg')))
    # set page precision
    if tot_files < 1000:
        pg_sigfigs = 3
    else:
        pg_sigfigs = 4
    for file in sorted(glob.glob(os.path.join(base_dir,output,'*.jpg'))):
        print(file)
        # process image
        proc_file = process_image(file, cnt, os.path.join(base_dir,output), pg_sigfigs, debug)
        # build up list of processed files
        files.append(proc_file)
        # add one to count
        cnt += 1
    # zip files
    zipdir(files, output, base_dir)
    # tidy up
    for file in files:
        os.remove(file)
    os.rmdir(os.path.join(base_dir, output, 'cropped'))
    for file in glob.glob(os.path.join(base_dir,output,'*.jpg')):
        os.remove(file)
    time.sleep(1.0)
    os.rmdir(os.path.join(base_dir, output))

if __name__ == '__main__':
    find_images_and_process('Eternals1')


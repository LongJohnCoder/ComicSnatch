# ComicSnatch

A little rough round the edges but it's a useful tool and utilises
 a bunch of cool modules like Selenium, OpenCV and BeautifySoup.
 
I've got to admit this tool was written with all the best intentions. 
I'd obtained a few "free" comic codes from my physics batch and couldn't
install the Marvel app on my aging tablet. So I decided to do some
webscraping and snatch them using some headless chromium browser and
cool python.

You'll find some bits are hardcoded and I'll tidy it up in due course
but thought I'd lost it so Github is my backup :)

### Future Uses
- chrome_screenshot's pretty epic at taking stills from a URL.
- auto_crop can remove the black letter box from a picture.
- batch_comics nothing note worthy at all, just a simple loop
  but this could be expanded to read from an RSS feed or JSON file.

### To note:
You could use this for other means, I've just not got round to implenting
other uses.

For use as is just:
- Install the dependencies
- Point to an install of the 'chromedriver'
- Login to Marvel (local cache is used)
- Point it at the comic URL you want to take offline

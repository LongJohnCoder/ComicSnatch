"""
Script to loop over chrome_screenshot
"""
from chrome_screenshot import GrabComics

comic_urls = [r'https://read.marvel.com/#/book/48246',
              r'https://read.marvel.com/#/book/43227,
              ]

for i, comic_url in enumerate(comic_urls):
    # if i == 0:
    login_url = "https://www.marvel.com/signin"
    comic = GrabComics(login_url=login_url,
                       url=comic_url,
                       # output=save_name,
                       redirect_url="https://www.marvel.com/",
                       series_mode=False,
                       headless=False
                       )
    # read all of the comic(s)
    #driver = comic.read_all()
    comic.read_all()
    #comic.clean_close()
    

import requests
import os

def persist_image(folder_path:str, urls:list, item, counter=0):
    loc = os.path.join(folder_path, item)
    if not os.path.exists(loc):
        os.makedirs(loc)
    for url in urls:
        try:
            image_content = requests.get(url).content
        except Exception as e:
            print(f"ERROR - Couldn't download {url} - as {loc}")

        try:
            f = open(os.path.join(loc, f"{item}_{counter}.jpg"), "wb")
            f.write(image_content)
            f.close()
            print(f"SUCCESS - saved {url} - as {loc}")

        except Exception as e:
            print(f"ERROR - couldn't save {url} -{e}")

        counter += 1
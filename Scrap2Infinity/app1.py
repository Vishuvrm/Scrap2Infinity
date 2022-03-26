from werkzeug.datastructures import FileStorage
import dill
dill.settings['recurse'] = True

with open(r"F:\WebScraping\Scrap2Infinity\static\uploads\fd37139a-ac38-11ec-bf88-2c6e85cb8233_wood.zip", "rb") as f:
    file = FileStorage(f)
    x = dill.dumps(file, protocol=5)
    y = "{0}".format(x)[1:]

    print(x)
    print(type(x))

    y = x.decode(encoding="UTF-32")
    # y = dill.loads(x)
    # y.save(r"F:\WebScraping\Scrap2Infinity\static\uploads\testing.zip")
    # y.close()

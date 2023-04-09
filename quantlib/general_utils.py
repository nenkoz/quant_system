import pickle


def save_file(path, obj):
    try:
        with open(path, "wb") as fp:
            pickle.dump(obj, fp)
    except Exception as err:
        print(err)


def load_file(path):
    try:
        with open(path, "rb") as fp:
            return pickle.load(fp)
    except Exception as err:
        print(err)


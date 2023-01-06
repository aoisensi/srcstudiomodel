from srcstudiomodel import VVD

with open("subject/frog.vvd", "rb") as file:
    vvd = VVD(file)
    print(vvd)
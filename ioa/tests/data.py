

f = open("access.txt", encoding="UTF-8")

c = f.read()
char1 = "?&data=%"
char2 = "403"
char3 = "499"

# x = c.rstrip("?&data=%")


stri_text = (c[c.find(char1)+8 : c.find(char2 or char3)])

# stri_text = stri_text.encode("UTF-8")

abc = bytes(stri_text.encode("UTF-8"))

print(abc)

y = abc.decode("UTF-8")
print(y)


import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import sys 
import pytesseract

def help():
    print("""
Page segmentation modes:
  0    Orientation and script detection (OSD) only.
  1    Automatic page segmentation with OSD.
  2    Automatic page segmentation, but no OSD, or OCR. (not implemented)
  3    Fully automatic page segmentation, but no OSD. (Default)
  4    Assume a single column of text of variable sizes.
  5    Assume a single uniform block of vertically aligned text.
  6    Assume a single uniform block of text.
  7    Treat the image as a single text line.
  8    Treat the image as a single word.
  9    Treat the image as a single word in a circle.
 10    Treat the image as a single character.
 11    Sparse text. Find as much text as possible in no particular order.
 12    Sparse text with OSD.
 13    Raw line. Treat the image as a single text line,
       bypassing hacks that are Tesseract-specific.

usage: python3 parsehocr.py pathToFile pathToOut """)

def parseArgv():
    # open image from argv[1]
    image = Image.open(sys.argv[1])

    # Create HOCR output in argv[2]
    hocr = pytesseract.image_to_pdf_or_hocr(image, config='--psm ' + sys.argv[3] , lang="por", extension='hocr')
    with open(sys.argv[2], 'w+b') as f:
        f.write(hocr) 
    
    return image

def parseHocr():
    # Generate ElementTree from hocr in argv[2]
    tree = ET.parse(sys.argv[2])
    
    root = tree.getroot() #root[0] = <head>; root[1] = <body>

    # advance root to the <body>
    root = root[1]

    # root[0] is now the first <div class='ocr_page'> 
    # root[1] would be the second <div class='ocr_page'> ?

    # TODO : if there are other pages needs to iterate over them to parse
    # sets page1 to the firt page in root
    page1 = root[0]
    data = {}
    # iterate by every child of page1 and extract paragraphs bbox coordinates every word to a dictionary indexed by paragraph id
    for child in page1.iter():
        if child.get('class') == 'ocr_par':
            # get all attributes from title into a list and discard the first (bbox)
            data[child.get('id')] = {'bbox':child.get('title').split()[1:],'text':""}
            last_par = child.get('id')
        if child.get('class') == 'ocrx_word':
            data[last_par]['text'] += child.text + " " #if x_wconf > k ?

    # cleanup paragraphs of only whitespaces
    for par in list(data.keys()):
        if data[par]['text'].isspace():
            del data[par]
    
    return data 

def parseHocrv2():
    # Generate ElementTree from hocr in argv[2]
    tree = ET.parse(sys.argv[2])
    root = tree.getroot()[1] #root[0] = <head>; root[1] = <body>
    page1 = root[0] # TODO : if there are other pages needs to iterate over them to parse #for page in root?
    page1data = {}
    
    last_carea = last_par = last_line = ""
    
    for child in page1.iter():
        if child.get('class') == 'ocr_carea':
            last_carea = child.get('id')
            page1data[last_carea] = {'bbox':child.get('title').split()[1:], 'paragraphs':{}}
        elif child.get('class') == 'ocr_par':
            last_par = child.get('id')
            page1data[last_carea]['paragraphs'][last_par] = {'bbox':child.get('title').split()[1:], 'lang':child.get('lang'), 'lines':{}}
        elif child.get('class') == 'ocr_line' or child.get('class') == 'ocr_textfloat' or child.get('class') == 'ocr_header' or child.get('class') == 'ocr_caption':
            last_line = child.get('id')
            page1data[last_carea]['paragraphs'][last_par]['lines'][last_line] = {'bbox':child.get('title').split()[1:4], 'x_size':child.get('title').split()[9], 'words':[], 'isCaption':False}
        elif child.get('class') == 'ocrx_word':
            page1data[last_carea]['paragraphs'][last_par]['lines'][last_line]['words'].append(child.text)

    return page1data 

def extractPhotos():
    # Generate ElementTree from hocr in argv[2]
    tree = ET.parse(sys.argv[2])
    root = tree.getroot() #root[0] = <head>; root[1] = <body>

    # TODO : if there are other pages needs to iterate over them to parse
    # sets page1 to the firt page in root
    page1 = root[1][0]
    
    # list that will hold the tupples(photo_id, [box coordinates])
    photos = []
    # iterate by every child of page1 and extract paragraphs bbox coordinates every word to a dictionary indexed by paragraph id
    for child in page1.iter():
        if child.get('class') == 'ocr_photo':
            photos.append((child.get('id'), child.get('title').split()[1:]))

    image = Image.open(sys.argv[1])
    for p in photos:
        tmpImage = image.crop((int(p[1][0]), int(p[1][1]), int(p[1][2]), int(p[1][3])))
        tmpImage.save("out/" + p[0] + ".jpg")
    
    return photos

def drawPhotosBoxes(image, photos):
    for p in photos:
        x, y, x2, y2 = int(p[1][0]), int(p[1][1]), int(p[1][2]), int(p[1][3])        
        ImageDraw.Draw(image).rectangle([x, y, x2, y2], fill=None, outline='red')

def drawParagraphBoxes(image, data):
    # draw paragraph boxes
    for par in data:    
        x, y, x2, y2 =  int(data[par]['bbox'][0]), int(data[par]['bbox'][1]), int(data[par]['bbox'][2]), int(data[par]['bbox'][3])
        ImageDraw.Draw(image).rectangle([x, y, x2, y2], fill=None, outline='green')

def drawBoxes(image, data, photos):
    drawPhotosBoxes(image, photos)    
    drawParagraphBoxes(image, data)
    image.show()

def writeToTxt(data):
    f = open("out/out.txt", 'w')
    for d in data:
        f.write(f"{d}, {data[d].get('bbox')}, {data[d].get('text')}")
        f.write("\n")

def writeToTxtv2(data):
    f = open("out/out.txt", 'w')
    for carea in data:
        f.write(f"{carea}:bbox{data[carea]['bbox']}\n")
        for par in data[carea]['paragraphs']:
            f.write(f"\t {par}:bbox{data[carea]['paragraphs'][par]['bbox']}\n")
            for line in data[carea]['paragraphs'][par]['lines']: 
                f.write("\t\t" + " ".join(data[carea]['paragraphs'][par]['lines'][line]['words']) + "\n")

def main():

    if (len(sys.argv) == 1) : 
        help()
        return 
    image = parseArgv()
    data = parseHocrv2()
    writeToTxtv2(data)
    breakpoint() 
    photos = extractPhotos()
    drawBoxes(image, data, photos)
    writeToTxt(data)
if __name__ == "__main__":
    main()

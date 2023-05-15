import sys
from PIL import Image, ImageDraw
import xml.etree.ElementTree as ET
import pytesseract
import copy


class Page:
    def __init__(self, id):
        self.id = id
        self.careas = []
        self.careasIdx = -1
        self.photos = []
        self.photosIdx = -1

    def addCarea(self, carea):
        self.careasIdx += 1
        self.careas.append(carea)

    def addPhoto(self, photo):
        self.photosIdx += 1
        self.photos.append(photo)

    def addPar(self, par): self.careas[self.careasIdx].addPar(par)
    def addLine(self, line): self.careas[self.careasIdx].addLine(line)
    def addWord(self, word): self.careas[self.careasIdx].addWord(word)


class Carea:
    def __init__(self, id, bbox):
        self.id = id
        self.bbox = bbox
        self.pars = []
        self.parsIdx = -1

    def addPar(self, par):
        self.parsIdx += 1
        self.pars.append(par)

    def addLine(self, line): self.pars[self.parsIdx].addLine(line)
    def addWord(self, word): self.pars[self.parsIdx].addWord(word)


class Par:
    def __init__(self, id, bbox, lang):
        self.id = id
        self.bbox = bbox
        self.lang = lang
        self.lines = []
        self.linesIdx = -1

    def addLine(self, line):
        self.linesIdx += 1
        self.lines.append(line)

    def addWord(self, word): self.lines[self.linesIdx].addWord(word)


class Line:
    def __init__(self, id, bbox, x_size):
        self.id = id
        self.bbox = bbox
        self.x_size = x_size
        self.words = []
        self.wordsIdx = -1

    def addWord(self, word):
        self.wordsIdx += 1
        self.words.append(word)


class Word:
    def __init__(self, id, bbox, x_wconf, text):
        self.id = id
        self.bbox = bbox
        self.x_wconf = x_wconf
        self.text = text


class Photo:
    def __init__(self, id, bbox):
        self.id = id
        self.bbox = bbox

    def getId(self): return self.id
    def getBbox(self): return self.bbox


def parseArgv():
    # open image from argv[1]
    image = Image.open(sys.argv[1])

    # Create HOCR output in argv[2]
    hocr = pytesseract.image_to_pdf_or_hocr(image, config='--psm ' + sys.argv[3], lang="por", extension='hocr')
    with open(sys.argv[2], 'w+b') as f:
        f.write(hocr)

    return image


def parseHocr():
    # Generate ElementTree from hocr in argv[2]
    tree = ET.parse(sys.argv[2])
    root = tree.getroot()[1]    # root[0] = <head>; root[1] = <body>

    page1 = root[0]     # TODO : if there are other pages needs to iterate over them to parse #for page in root?

    p1 = Page(page1.get('id'))
    for child in page1.iter():
        ocr_class = child.get('class')
        title = child.get('title').split()

        for idx in range(len(title)):
            if title[idx] == 'bbox':
                bbox = [int(title[idx+1]), int(title[idx+2]), int(title[idx+3])]
                if title[idx+4][-1] == ';':
                    bbox.append(int(title[idx+4][:-1]))
                else:
                    bbox.append(int(title[idx+4]))
            if title[idx] == 'x_size':
                x_size = float(title[idx+1][:-1])
            if title[idx] == 'x_wconf':
                x_wconf = int(title[idx+1])

        match ocr_class:
            case 'ocr_carea':
                p1.addCarea(Carea(child.get('id'), bbox))
            case 'ocr_par':
                p1.addPar(Par(child.get('id'), bbox, child.get('lang')))
            case 'ocr_line' | 'ocr_textfloat' | 'ocr_header' | 'ocr_caption':
                p1.addLine(Line(child.get('id'), bbox, x_size))
            case 'ocrx_word':
                p1.addWord(Word(child.get('id'), bbox, x_wconf, child.text))
            case 'ocr_photo':
                p1.addPhoto(Photo(child.get('id'), bbox))

    return p1


def removeCarateresNS(pageObject):
    
    carateres = ["@","#","$","%","&","*","|"]
    for carea in pageObject.careas:
        for par in carea.pars:
            for line,indexLn in zip(par.lines, range(0,len(par.lines))):
                for word,indexWrd in zip(line.words, range(0,len(line.words))):
                    if word.text in carateres:
                        if len(line.words) == 1:
                            del(par.lines[indexLn])
                        else:
                            del(line.words[indexWrd])

    return pageObject

def cleanTxt(pageObject):
    
    for carea in pageObject.careas:
        for par,indexPar in zip(carea.pars, range(0,len(carea.pars))):
            for index in range(0,len(par.lines)):
                if par.lines[index].words[-1].text[-1] == '-':
                    if len(carea.pars) > (indexPar+1) and index + 1 > len(par.lines) - 1:
                        carea.pars[indexPar+1].lines[0].words[0].text = par.lines[index].words[-1].text[:-1] + carea.pars[indexPar+1].lines[0].words[0].text
                        par.lines[index].words.pop()
                    elif index + 1 <= len(par.lines) - 1:
                        par.lines[index + 1].words[0].text = par.lines[index].words[-1].text[:-1] + par.lines[index + 1].words[0].text
                        par.lines[index].words.pop()
                    #ter em atencao de alguma lista de words fica vazia (nao esta feito)
    return pageObject

def confCheck(pageObject, conf):
    #se na mesma linha houver uma palavra com conf > "conf" deixar linha, se nao, remover

    for carea in pageObject.careas:
        for par in carea.pars:
            for line in par.lines:
                for word in line.words:
                    if word.x_wconf < conf:
                        del(line)
                        if len(carea.pars) == 0:
                            del(par)
                        break
    return pageObject

def letterType(pageObject):
    
    tamanhos = []
    for carea in pageObject.careas:
        for par in carea.pars:
            for line in par.lines:
                if line.x_size not in tamanhos:
                    tamanhos.append(line.x_size)

    return print(len(tamanhos)), print(tamanhos)


def drawCareaBoxes(image, pageObject):
    for carea in pageObject.careas:
        x, y, x2, y2 = carea.bbox[0] ,carea.bbox[1], carea.bbox[2], carea.bbox[3]
        ImageDraw.Draw(image).rectangle([x, y, x2, y2], fill=None, outline='red', width=3)


def drawParBoxes(image, pageObject):
    for carea in pageObject.careas:
        for paragraph in carea.pars:
            x, y, x2, y2 = paragraph.bbox[0], paragraph.bbox[1], paragraph.bbox[2], paragraph.bbox[3]
            ImageDraw.Draw(image).rectangle([x, y, x2, y2], fill=None, outline='blue', width=2)


def drawLinesBoxes(image, pageObject):
    for carea in pageObject.careas:
        for paragraph in carea.pars:
            for line in paragraph.lines:
                x, y, x2, y2 = line.bbox[0], line.bbox[1], line.bbox[2], line.bbox[3]
                ImageDraw.Draw(image).rectangle([x, y, x2, y2], fill=None, outline='green')


def drawPhotosBoxes(image, pageObject):
    for photo in pageObject.photos:
        x, y, x2, y2 = photo.bbox[0], photo.bbox[1], photo.bbox[2], photo.bbox[3]
        ImageDraw.Draw(image).rectangle([x, y, x2, y2], fill=None, outline='purple')


def drawArticlesBoxes(image, artigos):
    for artigo in artigos:
        x, y, x2, y2 = artigo.bbox[0], artigo.bbox[1], artigo.bbox[2], artigo.bbox[3]
        ImageDraw.Draw(image).rectangle([x, y, x2, y2], fill=None, outline='blue', width=2)


def extractPhotos(image, pageObject):
    for photo in pageObject.photos:
        x, y, x2, y2 = photo.bbox[0], photo.bbox[1], photo.bbox[2], photo.bbox[3]
        tmpImage = image.crop((x, y, x2, y2))
        tmpImage.save("out/" + photo.id + ".jpg")

    for carea in pageObject.careas:
        print(f"Carea: id:{carea.id} bbox:{carea.bbox}")
        for par in carea.pars:
            print(f"\tParagraph: id:{par.id} bbox:{par.bbox} lang:{par.lang}")
            for line in par.lines:
                print(f"\t\tLine: id:{line.id} bbox:{line.bbox} x_size:{line.x_size}")
                print(f"\t\t\tWords: {' '.join([word.text for word in line.words])}")


# Carea: id, bbox, pars[Par], parsIdx
# Par: id, bbox, lang, lines[Line], linesIdx
# Line: id, bbox, x_size, words[Word], wordIdx
# Word: id, bbox, x_wconf, text

# articles is a list of careas
def createArticles(pageObject):
    articles = copy.deepcopy(pageObject.careas)
    return articles


def organizeArticles(articles):
    toRemove = []
    for idx in range(len(articles) - 1):
        # if x_size1 > x_size2
        print(articles[idx].pars[0].lines[0].x_size ,articles[idx+1].pars[0].lines[0].x_size)
        if articles[idx].pars[0].lines[0].x_size > articles[idx+1].pars[0].lines[0].x_size:
            print('toRemove')
            articles[idx].pars += articles[idx+1].pars
            toRemove.append(articles[idx+1].id)
        # if bbox1 is shorter than bbox2
        #if articles[idx].bbox[2] < articles[idx+1].bbox[2]:
        #    articles[idx].pars += articles[idx+1].pars
        #    toRemove.append(articles[idx+1].id)

    for article in articles:
        if article.id in toRemove:
            articles.remove(article)

    return articles


def createMarkdown(articles):
    f = open("out/out.txt", 'w')
    for article in articles:
        f.write("\n\n___\n\n")
        for par in article.pars:
            for line in par.lines:
                f.write(" ".join([word.text for word in line.words]) + "\\\n")
            f.write("\n")


def main():
    image = parseArgv()
    page1 = parseHocr()

    articles = removeCarateresNS(page1)
    articlesSC = cleanTxt(articles)
    articlesConf = confCheck(articlesSC,30)
    articlesClearConf = createArticles(articlesConf)
    
    #letterType(page1)

    # articles = organizeArticles(articles)
    
    createMarkdown(articlesClearConf)

    # drawCareaBoxes(image, page1)
    # drawParBoxes(image, page1)
    # drawLinesBoxes(image, page1)
    # drawPhotosBoxes(image, page1)
    
    ##drawArticlesBoxes(image, articles)

    ##image.show()


    # extractPhotos(image, page1)


if __name__ == "__main__":
    main()

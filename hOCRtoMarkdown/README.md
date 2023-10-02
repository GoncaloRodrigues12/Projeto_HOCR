# hOCRtoMarkdown

**_Synopsis_**: hocr2md sourceImage [OPTION]

**_Description_**: Converts image into hocr file, via tesseract, and hocr into markdown.
    
        -h, --help              display this help menu
        
        -o, --output            choose name and location to output markdown file (location must exist)

        -e, --extractImages     extract images into nameOfInputFile_Images/

        -p, --psm               choose psm to be used by tesseract (default=3)

        -l, --lang              choose language to be used by tesseract (default=por)

        --extractImagesFolder   choose folder to extract images
        
        --conf                  choose value for line confidence (default=40, line is deleted if below confidence)
        
        --dc                    show image with Careas limits drawn

        --dp                    show image with Pars limits drawn

        --dl                    show image with Lines limits drawn

        --di                    show image with Images limits drawn

        --da                    show image with Articles limits drawn

**_Some page segmentation modes:_**

         1                      Automatic page segmentation with OSD.
         3                      Fully automatic page segmentation, but no OSD. (Default)
         4                      Assume a single column of text of variable sizes.
         5                      Assume a single uniform block of vertically aligned text.
         6                      Assume a single uniform block of text.
        11                      Sparse text. Find as much text as possible in no particular order.
        13                      Raw line. Treat the oppenedImage as a single text line,
                                bypassing hacks that are Tesseract-specific.


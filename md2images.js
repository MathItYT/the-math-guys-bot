const { Marked } = require('marked');
const fs = require('fs');
const hljs = require('highlight.js');
const { markedHighlight } = require('marked-highlight');
const markedKatex = require('marked-katex-extension');
const puppeteer = require('puppeteer');
const { PDFiumLibrary } = require('@hyzyla/pdfium');
const sharp = require('sharp');

async function renderFunction(options) {
    return await sharp(options.data, {
        raw: {
        width: options.width,
        height: options.height,
        channels: 4,
        },
    })
        .png()
        .toBuffer();
}

const main = async () => {
    if (fs.existsSync('images')) {
        fs.rmdirSync('images', { recursive: true });
    }
    fs.mkdirSync('images');
    const marked = new Marked(
        markedHighlight({
            emptyLangClass: 'hljs',
            langPrefix: 'hljs language-',
            highlight: (code, lang, info) => {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                return hljs.highlight(code, { language }).value;
            }
        }),
        markedKatex()
    );
    const markdown = fs.readFileSync('math.md', 'utf-8');
    const html = `<!DOCTYPE html>
<html>
  <head>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" integrity="sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+" crossorigin="anonymous">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.10.0/styles/github-dark.min.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap" rel="stylesheet">
  <style>
      * {
          color: #ebebeb;
      }
      body {
          background-color: #161616;
      }
      p, h1, h2, h3, h4, h5, h6, strong, tr, th, td, blockquote, a {
            font-family: 'Roboto', sans-serif;
        }
  </style>
  </head>
  <body>
    ${marked.parse(markdown)}
  </body>
</html>`;
    const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const page = await browser.newPage();
    await page.setContent(html);
    await setTimeout(() => {}, 5000);
    await page.pdf({
        path: 'math.pdf',
        margin: { top: '0px', right: '0px', bottom: '0px', left: '0px' },
        printBackground: true,
        format: 'A4',
    });
    await browser.close();
    const buff = fs.readFileSync('math.pdf');
    const library = await PDFiumLibrary.init();

    const document = await library.loadDocument(buff);

    for (const page of document.pages()) {
        console.log(`${page.number} - rendering...`);

        const image = await page.render({
            scale: 3,
            render: renderFunction,
        });

        fs.writeFileSync(`images/math-${page.number}.png`, Buffer.from(image.data));
    }

    document.destroy();
    library.destroy();
};

main();

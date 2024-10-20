const { Marked } = require('marked');
const fs = require('fs');
const hljs = require('highlight.js');
const { markedHighlight } = require('marked-highlight');
const markedKatex = require('marked-katex-extension');

const main = () => {
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
          width: 3840px;
        height: 2160px;
      }
      p, h1, h2, h3, h4, h5, h6 {
            font-family: 'Roboto', sans-serif;
        }
  </style>
  </head>
  <body>
    ${marked.parse(markdown)}
  </body>
</html>`;
    fs.writeFileSync('math.html', html);
};

main();

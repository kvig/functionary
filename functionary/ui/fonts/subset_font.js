const pathModule = require('path');
const { readFile } = require('fs').promises;
const fs = require('fs')
const fontkit = require('fontkit');
const subsetFont = require('subset-font');

readFile(
    pathModule.resolve(__dirname, 'Playball-Regular.ttf')
).then(sfntFont => {
    // Create a new font with only the characters required to render "F" in WOFF2 format:
    return subsetFont(sfntFont, 'F', {
        targetFormat: 'woff2',
    })
}).then(fnt => {
    console.log("Writing font to: ", process.argv[2])
    fs.writeFileSync(process.argv[2], fnt)
});
#!/usr/bin/env node
var args, NodeInterval, ni;

args = process.argv.splice(2);
NodeInterval = require('NodeInterval');

ni = new NodeInterval.Watcher({
    watchFolder: 'pages/calit2/templates/',
    inputFile: 'pages/calit2/index.html',
    replacementString: '@templates@',
    outputFile: 'pages/calit2/index_deploy.html'
});

// Pass "--watch" from command line to keep the proccess going.
if (args[0] == '--watch'){
   ni.startWatch();
}

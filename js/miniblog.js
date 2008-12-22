// CheckNerds miniBlog Widget
// 
// Derived from:
// 	Douban Miniblog Widget
// 	version: 0.2.1
// 	Copyright (c) 2008 Wu Yuntao <http://luliban.com/blog/>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
/*
var username = null;
var hidetitle = 'false';
var hidefooter = 'false';
var maxresults = '10';
var style = 'green';
var width = null;

var styleDict = {
    "black": {
        "borderColor": "rgb(170, 170, 170)",
        "bgColor": "rgb(0, 0, 0)",
        "titleBorderColor": "rgb(216, 219, 188)",
        "titleColor": "rgb(204, 204, 204)",
        "textColor": "rgb(122, 43, 14)",
        "linkColor": "rgb(221, 85, 34)",
        "footerBgColor": "rgb(17, 17, 17)",
        "footerLinkColor": "rgb(153, 153, 153)"
    },
    "blue": {
        "borderColor": "rgb(188, 204, 235)",
        "bgColor": "rgb(255, 255, 255)",
        "titleBorderColor": "rgb(188, 204, 235)",
        "titleColor": "rgb(9, 9, 146)",
        "textColor": "rgb(122, 126, 224)",
        "linkColor": "rgb(16, 16, 200)",
        "footerBgColor": "rgb(229, 236, 249)",
        "footerLinkColor": "rgb(137, 141, 233)"
    },
    "gray": {
        "borderColor": "rgb(204, 204, 204)",
        "bgColor": "rgb(255, 255, 255)",
        "titleBorderColor": "rgb(204, 204, 204)",
        "titleColor": "rgb(102, 102, 102)",
        "textColor": "rgb(204, 204, 204)",
        "linkColor": "rgb(153, 153, 153)",
        "footerBgColor": "rgb(238, 238, 238)",
        "footerLinkColor": "rgb(204, 204, 204)"
    },
    "green": {
        "borderColor": "rgb(216, 219, 188)",
        "bgColor": "rgb(255, 255, 255)",
        "titleBorderColor": "rgb(216, 219, 188)",
        "titleColor": "rgb(45, 133, 9)",
        "textColor": "rgb(151, 224, 122)",
        "linkColor": "rgb(88, 191, 47)",
        "footerBgColor": "rgb(245, 251, 235)",
        "footerLinkColor": "rgb(173, 176, 148)"
    },
    "khaki": {
        "borderColor": "rgb(142, 124, 106)",
        "bgColor": "rgb(242, 233, 202)",
        "titleBorderColor": "rgb(204, 187, 170)",
        "titleColor": "rgb(221, 85, 34)",
        "textColor": "rgb(187, 170, 153)",
        "linkColor": "rgb(85, 68, 51)",
        "footerBgColor": "rgb(234, 224, 198)",
        "footerLinkColor": "rgb(153, 136, 119)"
    },
    "pink": {
        "borderColor": "rgb(170, 170, 170)",
        "bgColor": "rgb(250, 250, 250)",
        "titleBorderColor": "rgb(221, 221, 221)",
        "titleColor": "rgb(221, 102, 153)",
        "textColor": "rgb(238, 187, 204)",
        "linkColor": "rgb(230, 132, 173)",
        "footerBgColor": "rgb(252, 240, 247)",
        "footerLinkColor": "rgb(170, 136, 136)"
    },
    "slate": {
        "borderColor": "rgb(51, 68, 85)",
        "bgColor": "rgb(17, 34, 51)",
        "titleBorderColor": "rgb(94, 111, 128)",
        "titleColor": "rgb(94, 128, 94)",
        "textColor": "rgb(94, 111, 128)",
        "linkColor": "rgb(170, 187, 204)",
        "footerBgColor": "rgb(21, 41, 57)",
        "footerLinkColor": "rgb(170, 187, 204)"
    },
    "none": { }
};*/

function getStyle(styleName) {
    eval("var current = styleDict." + styleName);
    if (typeof current == 'undefined') return styleDict.none;
    return current;
}

function iblog(json) {
    /*var _wrapperStyle = style == styleDict.none ? "" : 'style="' + (width ? 'width: ' + width + 'px;' : '') + 'border: 4px solid ' + style.borderColor + '; margin: 0.5em; padding: 0pt; background: ' + style.bgColor + ' none repeat scroll 0% 0%; -moz-background-clip: -moz-initial; -moz-background-origin: -moz-initial; -moz-background-inline-policy: -moz-initial; text-align: left; text-indent: 0pt; text-decoration: none; font-weight: normal; font-family: arial,sans-serif; font-size: 10pt; -moz-border-radius: 8px "';
    var _titleStyle = style == styleDict.none ? "" : 'style="border-style: none none solid; border-color: -moz-use-text-color -moz-use-text-color ' + style.titleBorderColor + '; border-width: medium medium 1px; margin: 0pt 0.5em; padding: 0.2em 0pt; background: transparent none repeat scroll 0% 0%; -moz-background-clip: -moz-initial; -moz-background-origin: -moz-initial; -moz-background-inline-policy: -moz-initial; text-align: left; text-indent: 0pt; text-decoration: none; font-weight: normal; -moz-border-radius: 8px; -moz-border-radius-bottomright: 0pt; -moz-border-radius-bottomleft: 0pt; color: ' + style.titleColor + ';"';
    var _listStyle = style == styleDict.none ? "" : 'style="border: medium none ; margin: 0pt 0.5em; padding: 0.2em; background: transparent none repeat scroll 0% 0%; overflow: hidden; -moz-background-clip: -moz-initial; -moz-background-origin: -moz-initial; -moz-background-inline-policy: -moz-initial; text-align: left; text-indent: 0pt; text-decoration: none; font-weight: normal;"';
    var _listItemStyle = style == styleDict.none ? "" : 'style="border: medium none ; margin: 0pt; padding: 0.4em 0pt; background: transparent none repeat scroll 0% 0%; -moz-background-clip: -moz-initial; -moz-background-origin: -moz-initial; -moz-background-inline-policy: -moz-initial; text-align: left; text-indent: 0pt; text-decoration: none; font-weight: normal; list-style-type: none; color: ' + style.textColor + '"';
    var _listLinkStyle = style == styleDict.none ? "" : 'style="border-style: none none solid; border-color: -moz-use-text-color -moz-use-text-color ' + style.textColor + '; border-width: medium medium 1px; margin: 0pt; padding: 0pt; background: transparent none repeat scroll 0% 0%; -moz-background-clip: -moz-initial; -moz-background-origin: -moz-initial; -moz-background-inline-policy: -moz-initial; text-align: left; text-indent: 0pt; text-decoration: none; font-weight: normal; color:' + style.linkColor + ';"';
    var _footerStyle = style == styleDict.none ? "" : 'style="border-style: solid none none; border-color: ' + style.borderColor + ' -moz-use-text-color -moz-use-text-color; border-width: 1px medium medium; margin: 0pt; padding: 0.2em 8px; background: ' + style.footerBgColor + ' none repeat scroll 0% 0%; -moz-background-clip: -moz-initial; -moz-background-origin: -moz-initial; -moz-background-inline-policy: -moz-initial; text-align: right; text-indent: 0pt; text-decoration: none; font-weight: normal; -moz-border-radius-topleft: 0pt; -moz-border-radius-topright: 0pt; -moz-border-radius-bottomright: 4px; -moz-border-radius-bottomleft: 4px; font-size: small; white-space: nowrap;"';
    var _footerLinkStyle = style == styleDict.none ? "" : 'style="border: medium none ; margin: 0pt; padding: 0pt; background: transparent none repeat scroll 0% 0%; -moz-background-clip: -moz-initial; -moz-background-origin: -moz-initial; -moz-background-inline-policy: -moz-initial; text-align: left; text-indent: 0pt; text-decoration: underline; font-weight: normal; color: ' + style.footerLinkColor + ';"';
*/
    //var _title = hidetitle == 'true' ? '' : '<h3 ' + _titleStyle + '>' + json.title.$t + '</h3>';
    //var _footer = hidefooter == 'true' ? '' : '<div ' + _footerStyle + '><a ' + _footerLinkStyle + ' href="' + json.author.link[1]['@href'] + '">' + json.author.name.$t + '的豆瓣主页</a></div>';
    //document.write('<div id="douban-miniblog" ' + _wrapperStyle + '>' + _title + '<ul ' + _listStyle + '>');
    //document.write('hello,world');
	document.write(json);
	/*for (var i = 0; i < json.length; i++) {
        //var html = json.entry[i].content.$t;
		var html=json[i];
		document.write(html);
        //html = html.replace(/href/g, _listLinkStyle + ' href');
        //document.write('<li ' + _listItemStyle + '>' + html + '</li>');
    }
    document.write('</ul>' + _footer + '</div>');*/
}

(function() {
    document.write('hello,world1');
    document.write('<script type="text/javascript" src="http://localhost:8080/service/badge/?userid=42&callback=iblog"></script>');
	/*var _script = null;
    var _params = null;
    var _var = null;
    var scriptTags = document.getElementsByTagName('script');
    for (var i = 0; i < scriptTags.length; i++) {
        _script = scriptTags[i];
        if (_script.src && _script.src.match(/miniblog\.js(\?.*)?$/)) {
            _params = _script.src.match(/\?(.*)$/)[1].toLowerCase().split('&');
            for (var j = 0; j < _params.length; j++) {
                _var = _params[j].split('=');
                eval(_var[0] + '="' + _var[1] + '"');
            }
            if (!username) throw new Error("``username`` is required");
            style = getStyle(style);
            //document.write('<script type="text/javascript" src="http://localhost:8080/service/badge/42"></script>')
            break;
        }
    }*/
})();

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

function getStyle(styleName) {
    eval("var current = styleDict." + styleName);
    if (typeof current == 'undefined') return styleDict.none;
    return current;
}

function iblog(json) {
    document.write('hello,iblog!');
  	document.write(json);
}

(function() {
    document.write('hello,world1');
    document.write('<script type="text/javascript" src="http://localhost:8080/service/badge/?userid=42&callback=iblog"></script>');
	//break;
})();

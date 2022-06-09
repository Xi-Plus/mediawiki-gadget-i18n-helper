import argparse
import html
import json
import re

import requests

parser = argparse.ArgumentParser()
parser.add_argument('files', nargs='+')
parser.add_argument('--uselang', default='zh-cn')
parser.add_argument('--mode', choices=['single', 'i18n'], default='single')
parser.add_argument('--function', default='wgULS')
args = parser.parse_args()
print(args)

run_files = args.files

noteTA = '''{{NoteTA
|G1=IT
|G2=MediaWiki
}}
-{H|zh-hans:帮助;zh-hant:說明}-
-{H|zh-hans:周;zh-hant:週}-
-{H|zh-hans:批复;zh-hant:批復}-
-{H|zh-hans:配置;zh-hant:配置}-
-{H|zh-hans:窗口;zh-hant:視窗}-
-{H|zh-hans:项目;zh-hant:項目}-
-{H|zh-hans:单击;zh-hant:點擊}-
-{H|zh-hans:支持;zh-hant:支援}-
-{H|zh-hans:标清;zh-hant:標清}-
-{H|zh-hans:移动设备;zh-hant:行動裝置}-
-{H|zh-hans:关联;zh-hant:關聯}-
-{H|zh-hans:保存;zh-hant:儲存}-
-{H|zh-hans:执行;zh-hant:執行}-
-{H|zh-hans:消息;zh-hant:訊息}-
-{H|zh-hans:启动;zh-hant:啟動}-
-{H|zh-hans:启用功能;zh-hant:啟用功能}-
-{H|zh-hans:启用;zh-hant:啟用}-
-{H|zh-hans:计划;zh-hant:計劃}-
-{H|zh-hans:不实资料;zh-hant:不實資料}-
-{H|zh-hans:注释;zh-hant:注釋}-
-{H|zh-hans:分辨率;zh-hant:解析度}-
-{H|zh-hans:类型;zh-hant:類別}-
-{H|zh-hans:账户;zh-hant:帳號}-
-{H|zh-hans:已在运行;zh-hant:已在執行}-
-{H|zh-hans:当前;zh-hant:目前}-
-{H|zh-hans:最近更改;zh-hant:近期變更}-
-{H|zh-hans:相关更改;zh-hant:相關變更}-
-{H|zh-hans:说明;zh-hant:說明}-
-{H|zh-hans:Twinkle帮助;zh-hant:Twinkle說明}-
-{H|zh-hans:公用IP;zh-hant:公共IP}-
-{H|zh-hans:监视;zh-hant:監視}-
-{H|zh-hans:通过;zh-hant:透過}-
-{H|zh-hans:链入;zh-hant:連入}-
-{H|zh-hans:消链;zh-hant:消連}-
-{H|zh-hans:品质;zh-hant:品質}-
-{H|zh-hans:命名空间;zh-hant:命名空間}-
-{H|zh-hans:存档;zh-hant:存檔}-
-{H|zh-hans:表单;zh-hant:表單}-
'''

headers = {
    'user-agent': 'mediawiki-gadget-i18n-helper'
}


def escapeWikitextMatch(text):
    return '&#{};'.format(ord(text[0]))


def escapeWikitext(text):
    text = re.sub(r"[\[\]{}<>|\\:*'_#&\s]", escapeWikitextMatch, text)
    return text


def convertMessages(messages, uselang):
    text = noteTA
    for key, message in messages.items():
        text += '<div id="text-{}">{}</div>'.format(key, escapeWikitext(message))

    data = {
        'action': 'parse',
        'format': 'json',
        'text': text,
        'prop': 'text',
        'contentmodel': 'wikitext',
        'uselang': uselang,
    }
    r = requests.post('https://zh.wikipedia.org/w/api.php', data=data, headers=headers)
    try:
        r_json = r.json()
    except Exception as e:
        print(e)
        print(r.text)
        return {}
    parsed_text = r_json['parse']['text']['*']

    matches = re.findall(r'<div id="text-(.+?)">(.+?)</div>', parsed_text)
    result = {}
    for match in matches:
        key = match[0]
        if key.isdigit():
            key = int(key)
        new_text = html.unescape(match[1]).replace('\\n', '\\\\n')

        result[key] = new_text
    return result


if args.mode == 'single':
    for filename in run_files:
        print(filename)

        with open(filename, 'r', encoding='utf8') as f:
            jstext = f.read()

        matches = re.findall(args.function + r"\(\s*'(.*?)',\s*?'((?:[^()]|\([^()]*?\))*?)'\s*\)", jstext)

        old_messages = []
        messages_to_convert = {}
        for match in matches:
            # print(match)
            if args.lang == 1:
                orimessage = match[0]
            else:
                orimessage = match[1]
            messages_to_convert[len(old_messages)] = orimessage
            old_messages.append((match[0], match[1]))

        converted_messages = convertMessages(messages_to_convert, args.uselang)

        for idx, newtext in converted_messages.items():
            # print(idx, newtext)
            if args.lang == 1:
                newregex = r'\g<1>\g<2>\g<3>{}\g<5>'.format(newtext)
            else:
                newregex = r'\g<1>{}\g<3>\g<4>\g<5>'.format(newtext)
            jstext = re.sub(
                r"(" + args.function + r"\(\s*')({})(',\s*?')({})('\s*\))".format(re.escape(old_messages[idx][0]), re.escape(old_messages[idx][1])),
                newregex,
                jstext,
            )

        jstext = re.sub(args.function + r"\(\s*'(.+?)',\s*?'\1'\s*\)", r"'\1'", jstext)

        with open(filename, 'w', encoding='utf8') as f:
            f.write(jstext)

elif args.mode == 'i18n':
    if len(run_files) != 2:
        print('Must be 2 files')
        exit()

    with open(run_files[0], 'r', encoding='utf8') as f:
        src_json = json.load(f)
    with open(run_files[1], 'r', encoding='utf8') as f:
        dst_json = json.load(f)
    converted_messages = convertMessages(src_json, args.uselang)
    for key, message in converted_messages.items():
        dst_json[key] = message

    with open(run_files[1], 'w', encoding='utf8') as f:
        json.dump(dst_json, f, ensure_ascii=False, indent='\t')

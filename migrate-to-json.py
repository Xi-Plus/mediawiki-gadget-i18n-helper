import argparse
import json
import re
from collections import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument('source')
parser.add_argument('target_hans')
parser.add_argument('target_hant')
parser.add_argument('--old_function', default='wgULS')
parser.add_argument('--new_function', default='$t')
args = parser.parse_args()
print(args)

with open(args.source, 'r', encoding='utf8') as f:
    source = f.read()
with open(args.target_hans, 'r', encoding='utf8') as f:
    target_hans = json.load(f)
with open(args.target_hant, 'r', encoding='utf8') as f:
    target_hant = json.load(f)

matches = re.findall(args.old_function + r"\(\s*'(.*?)',\s*?'((?:[^()]|\([^()]*?\))*?)'\s*\)", source)

try:
    for match in matches:
        print(match)
        while True:
            key = input('input key: ')
            if key in target_hans and target_hans[key] == match[0] and key in target_hant and target_hant[key] == match[1]:
                break
            if key not in target_hans or key not in target_hant:
                break
            if key in target_hans:
                print('The key exists in hans: {}'.format(target_hans[key]))
            if key in target_hant:
                print('The key exists in hans: {}'.format(target_hant[key]))

        source = re.sub(
            r"(" + args.old_function + r"\(\s*')({})(',\s*?')({})('\s*\))".format(re.escape(match[0]), re.escape(match[1])),
            "{}('{}')".format(args.new_function, key),
            source,
        )
        target_hans[key] = match[0]
        target_hant[key] = match[1]
except KeyboardInterrupt:
    pass

matches = (
    re.findall(re.escape(args.new_function) + r"\('(.+?)'\)", source)
    + re.findall(re.escape(args.new_function) + r"\('(.+?)',", source)
    + re.findall(r'<i18n-t keypath="(.+?)"', source)
)
key_idx = {}
for match in matches:
    if match not in key_idx:
        key_idx[match] = source.index(match)

target_hans = OrderedDict(sorted(target_hans.items(), key=lambda v: key_idx.get(v[0], 0)))
target_hant = OrderedDict(sorted(target_hant.items(), key=lambda v: key_idx.get(v[0], 0)))

print('Write to files')
with open(args.source, 'w', encoding='utf8') as f:
    f.write(source)
with open(args.target_hans, 'w', encoding='utf8') as f:
    json.dump(target_hans, f, ensure_ascii=False, indent=2)
with open(args.target_hant, 'w', encoding='utf8') as f:
    json.dump(target_hant, f, ensure_ascii=False, indent=2)

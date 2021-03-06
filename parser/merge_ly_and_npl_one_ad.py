#!/usr/bin/python
# -*- coding: utf-8 -*
import re
import json
import codecs
import argparse

import common


parser = argparse.ArgumentParser(description='Specify an ad number.')
parser.add_argument('--ad', dest='ad', action='store_const', const=9, help='Specify an ad number')
# ly.gov.tw didn't have legislators information of ad=1, might need some warning
args = parser.parse_args(['--ad'])


def find_legislator_from_ly_info(names, term, ly_dict_list):
    possible = [legislator for legislator in ly_dict_list if legislator["ad"] == term["ad"] and legislator["name"] in names]
    if len(possible) == 1:
        return possible[0]
    elif len(possible) == 0:
        print 'ly2npl can not find legislator at ad: %s named: %s' % (str(term["ad"]), names[0])
    else:
        print 'ly2npl duplicate name in: %s at ad: %s' % (names[:], str(term["ad"]))
        possible2one = [legislator for legislator in possible if legislator["party"] == term["party"] and legislator["gender"] == term["gender"]]
        if len(possible2one) == 1:
            return possible2one[0]
        else:
            print 'ly2npl still can not find only one legislator from possible list!!'

def find_legislator_from_npl(ly_legislator, origin_npl_dict_list):
    possible = [legislator for legislator in origin_npl_dict_list if legislator["name"] == ly_legislator["name"] and legislator["ad"] == ly_legislator["ad"]]
    if len(possible) == 1:
        return possible[0]
    elif len(possible) == 0:
        print 'npl2ly can not find legislator at ad: ' + str(ly_legislator["ad"]) + ' named: ' + ly_legislator["name"]
    else:
        print 'npl2ly duplicate name: ' + ly_legislator["name"] + ' at: ' + str(ly_legislator["ad"])
        possible2one = [legislator for legislator in possible if legislator["party"] == ly_legislator["party"] and legislator["gender"] == ly_legislator["gender"]]
        if len(possible2one) == 1:
            return possible2one[0]
        else:
            print 'npl2ly still can not find only one legislator from possible list!!'

def complement(addition, base):
    # use npl as base information, if column that npl didn't has, use ly.gov.tw as complement
    pairs = [(key, value) for key, value in addition.items() if not base.has_key(key)]
    base.update(pairs)
    base["constituency"] = addition["constituency"]
    if base["ad"] != 1:
        base["experience"] = addition["experience"]
    return base

def conflict(compare, base, f):
    for key in ["gender", "in_office",]:
        if compare.has_key(key) and base.has_key(key):
            if compare[key] != base[key]:
                f.write('key, %s, (ly.gov.tw), %s, (npl), %s, uid, %s, ad, %s, name, %s, links, %s\n' % (key, compare[key], base[key], base["uid"], base["ad"], base["name"], compare["links"]["ly"]))
        else:
            f.write('can not find key: %s\n' % key)

ly_dict_list = json.load(open('../data/%d/ly_info.json' % args.ad))
npl_dict_list = json.load(open('../data/%d/npl_ly.json' % args.ad))
for source in [ly_dict_list, npl_dict_list]:
    for legislator in source:
        common.normalize_name(legislator)
for npl_legislator in npl_dict_list:
    names_list = [npl_legislator["name"]]
    for name in npl_legislator.get("former_names", []):
        names_list.append(name)
    ly_legislator = find_legislator_from_ly_info(names_list, npl_legislator, ly_dict_list)
    if ly_legislator:
        term = complement(ly_legislator, npl_legislator)
# --> cross check data conflict
f = codecs.open('../log/conflict.txt','w', encoding='utf-8')
for ly_legislator in ly_dict_list:
    npl_legislator = find_legislator_from_npl(ly_legislator, npl_dict_list)
    if npl_legislator:
        conflict(ly_legislator, npl_legislator, f)
f.close()
# <-- end

dump_data = json.dumps(npl_dict_list, sort_keys=True, ensure_ascii=False)
common.write_file(dump_data, '../data/%d/merged.json' % args.ad)
dump_data = json.dumps(npl_dict_list, sort_keys=True, indent=4, ensure_ascii=False)
common.write_file(dump_data, '../data/pretty_format/%d/merged.json' % args.ad)

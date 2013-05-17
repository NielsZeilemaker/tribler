#!/usr/bin/env python2

import os
import libxml2
import pprint
import codecs
import json

def parse(doc):
    ctxt = doc.xpathNewContext()
    ctxt.xpathRegisterNs("tva", "urn:tva:metadata:2011")
    ctxt.xpathRegisterNs("mpeg7", "urn:tva:mpeg7:2008")
    owner_x = ctxt.xpathEval("/tva:TVAMain/tva:MetadataOriginationInformationTable/tva:MetadataOriginationInformation/tva:RightsOwner")
    basic_description_x = ctxt.xpathEval("/tva:TVAMain/tva:ProgramDescription/tva:ProgramInformationTable/tva:ProgramInformation/tva:BasicDescription")[0]
    url_x = ctxt.xpathEval("/tva:TVAMain/tva:ProgramDescription/tva:ProgramLocationTable/tva:OnDemandService/tva:OnDemandProgram/tva:ProgramURL")[0]
    rev_x = ctxt.xpathEval("/tva:TVAMain/tva:ProgramDescription/tva:ProgramReviewTable/tva:Review")
    users_x = ctxt.xpathEval("/tva:TVAMain/tva:ProgramDescription/tva:ProgramReviewTable/ReviewerData/Reviewer")

    def format_review(ctxt, r):
        ctxt.setContextNode(r)

        revert = ctxt.xpathEval("Spam")[0].content
        text = ctxt.xpathEval("tva:FreeTextReview")[0].content
        text = unicode(text, 'utf-8')
        return dict(revert=revert, text=text)

    owner = owner_x[0].content

    ctxt.setContextNode(basic_description_x)
    title = ctxt.xpathEval("tva:Title")[0].content
    sypnosis = ctxt.xpathEval("tva:Synopsis")[0].content if len(ctxt.xpathEval("tva:Synopsis")) > 0 else None
    keywords = [kw.content for kw in ctxt.xpathEval("tva:Keyword")]
    genre = ctxt.xpathEval("tva:Genre/tva:Name")[0].content
    url = url_x.content

    reviews = [format_review(ctxt, r) for r in rev_x]
    video = dict(name=title, modifications=reviews)

    return video

def load_data(path1):
    videos = []
    for path in [path1]:
        for fname in os.listdir(path):
            if fname.endswith(".xml"):
                # print path + fname
                data = codecs.open(path + fname, encoding='utf-8-sig').read().encode("utf-8")
                # print data.encode("utf-8")
                doc = libxml2.parseDoc(data)
                video = parse(doc)
                doc.freeDoc()

                videos.append(video)

    return videos

def dump_data(basedir, videos, path):
    """Dumps only the reviews into JSON format"""
    with open(basedir + path, "w") as f:
        json.dump(videos, f, sort_keys=True, indent=4)

def main():
    import sys
    basedir = sys.argv[1]
    print "Loading data."
    videos = load_data(basedir)
    print "Dumping data."
    dump_data("./", videos, "comments.json")

if __name__ == "__main__":
    main()

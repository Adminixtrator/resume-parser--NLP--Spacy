# -*- coding: utf-8 -*-

import en_core_web_sm   
import fitz
from spacy.pipeline import EntityRuler
import jsonlines
import math
import re


regex = re.compile(u'\u25CF|\u2022|\u25E6|\u2023|\u2219|\u25CB')
emailR = re.compile(r'\w+[.|\w]\w+@\w+[.]\w+[.|\w+]\w+')
lnkdR = re.compile(r'linkedin.com/in/\w+')
dateR = re.compile(r'\w+\s\d{4}\s\w{2,4}\s\w+\s\w{0,4}|\w+\s\d{4}\s\D+\s\w+\s\w{0,4}')
dateFR = re.compile(r'\w+\s\d{4}\s\w{2,4}\s\w+\s\w{0,4}\s\(|\w+\s\d{4}\s\D+\s\w+\s\w{0,4}\s\(')
nlp = en_core_web_sm.load()

def clean_text(corpus):
        cleaned_text = ""
        for i in corpus:
            cleaned_text = cleaned_text + i.lower().replace("'", "")
        return cleaned_text

class TextExtract():

    def extract_text_from_pdf(file):
        content = ""
        cnt = 0
        doc = fitz.open(file)
        while cnt < doc.pageCount:
            page = doc.loadPage(cnt)
            content = content + page.getText("resume_raw_text")
            cnt+=1
        return content.strip(), clean_text(content.strip().replace("\n", " ").replace("\t", " "))

def create_skill_set(doc):
    return set([ent.label_[6:] for ent in doc.ents if 'skill' in ent.label_.lower()])

def create_skillset_dict(resume_texts):
    skillsets = [create_skill_set(resume_text) for resume_text in resume_texts]
    return skillsets

def create_skill_set_verb(doc):
    return set([ent.label_[5:] for ent in doc.ents if 'verb' in ent.label_.lower()])

def create_skillset_dict_verb(resume_texts):
    skillsets = [create_skill_set_verb(resume_text) for resume_text in resume_texts]
    return skillsets

def checkReadability(text):
    try:
        exp = [True for i in text.splitlines() if 'experience' in i.lower().split(" ") or 'projects' in i.lower().split(" ") and len(i.lower().split(" ")) <= 2][0]
    except IndexError:
        exp = False
    try:
        edu = [True for i in text.splitlines() if 'education' in i.lower().split(" ") or 'certifications' in i.lower().split(" ") and len(i.lower().split(" ")) == 1][0]
    except IndexError:
        edu = False
    try:
        sumr = [True for i in text.splitlines() if 'summary' in i.lower().split(" ") and len(i.lower().split(" ")) <= 2][0]
    except IndexError:
        sumr = False
    if exp is False or edu is False or sumr is False:
        return False
    else:
        return True
    
def checkEducation(text):
    try:
        for i in text.splitlines(): 
            if 'education' in i.lower().split(" ") and len(i.lower().split(" ")) == 1:
                return True, i.split(" ")[-1]
            elif 'certifications' in i.lower().split(" ") and len(i.lower().split(" ")) == 1:
                return True, i.split(" ")[-1]
            elif any("education" in j for j in i.lower().split(" ")) and len(i.lower().split(" ")) == 1: 
                return True, 'any("education" in j for j in i.lower().split(" ")) '
            elif any("certifications" in j for j in i.lower().split(" ")) and len(i.lower().split(" ")) == 1:
                return True, 'any("certifications" in j for j in i.lower().split(" "))'
            else:
                return False, '' 
    except IndexError:
        return False, ''

def checkExperience(text):
    try:
        for i in text.splitlines(): 
            if 'experience' in i.lower().split(" ") and len(i.split(" ")) <= 2:
                return True, i.split(" ")[-1]
            elif 'projects' in i.lower().split(" ") and len(i.split(" ")) <= 2:
                return True, i.split(" ")[-1]
            elif any("experience" in j for j in i.lower().split(" ")) and len(i.split(" ")) <= 2: 
                return True, any("experience" in j for j in i.lower().split(" "))
            elif any("projects" in j for j in i.lower().split(" ")) and len(i.split(" ")) <= 2:
                return True, any("projects" in j for j in i.lower().split(" "))
            else:
                return False, ''        
    except IndexError:
        return False, ''

def checkEmail(raw_text):
    if emailR.findall(raw_text) != []:
        return True, emailR.findall(raw_text)[0]
    else: 
        return False, ''

def checkLinkedin(raw_text):
    if lnkdR.findall(raw_text) != []:
        return True, lnkdR.findall(raw_text)[0]  
    else: 
        return False, ''

def checkReferees(text):
    try:
        for i in text.splitlines():
            if 'referees' in i.lower().split(" ") and len(i.lower().split(" ")) <= 1:
                return True
            elif 'references' in i.lower().split(" ") and len(i.lower().split(" ")) <= 1:
                return True
            else:
                return False
    except:
        return False

def checkSummary(text):
    try:
        for i in text.splitlines(): 
            if 'summary' in i.lower().split(" ") and len(i.lower().split(" ")) <= 2:
                return True
    except IndexError:
        return False

def checkObjective(text):
    for i in text.splitlines(): 
        if 'objectives' in i.lower().split(" ") and len(i.lower().split(" ")) <= 2:
            return True
        elif 'objective' in i.lower().split(" ") and len(i.lower().split(" ")) <= 2:
            return True
        else:
            return False


if __name__ == '__main__':

    resume = './'+input("Resume Filename: ")
    level = input("Level (Senior/Mid/Junior): ")
    responseJson = {}
    summaryRequired = False
    maxBulletPoints = 0
    sectionsScore = 0
    maxResumeLength = 0
    overallBrevity = 0
    if len(resume) <= 100:
        resume_raw_text, resume_text = TextExtract.extract_text_from_pdf(resume)
    actionVerbs = []
    if level.lower() == 'senior':
        summaryRequired = True
        maxBulletPoints = 52
        maxResumeLength = 2000
    if level.lower() == 'mid':
        summaryRequired = True
        maxBulletPoints = 42
        maxResumeLength = 1500
    if level.lower() == 'junior':
        summaryRequired = False
        maxBulletPoints = 32
        maxResumeLength = 1000
    f = open("actionVerbs.txt", "r")
    content = f.read()
    f.close()
    for i in content.splitlines():
        actionVerbs.append(i.lower())
    buzzWords = ["highly motivated", "strong leadership", "management skills", "extensive experience", "problem solver", "problem solving", "results-oriented", "hits the ground running", "process improvements", "ambitious", "seasoned", "customer driven", "extensive experience", "vast experience", "thought leader", "natural leader", "communication skills", "creative thinker", "savvy"]
    i = 0
    auxList = []
    impactList = []
    while i < len(resume_raw_text.splitlines()):
        try:
            if regex.findall(resume_raw_text.splitlines()[i]) != [] and regex.findall(resume_raw_text.splitlines()[i+1]) == [] and regex.findall(resume_raw_text.splitlines()[i-1]) == []:
                auxList.append(i)
            try:
                if (resume_raw_text.splitlines()[i]+ ' ' + resume_raw_text.splitlines()[i+1]).split()[1].lower() in actionVerbs or (resume_raw_text.splitlines()[i]+ ' ' + resume_raw_text.splitlines()[i+1]).split()[1].lower() == 'i':
                    impactList.append(i)
            except:
                pass
        except IndexError:
            break
        i += 1 
    dates = []
    dateScore = 0
    dtFormat = False
    noDates = False
    datesOrdered = False
    for i in dateR.findall(resume_text):
        dates.append(i.split(" ")[1])
    dtFormat = [True if len(dateFR.findall(resume_text)) > 0 else False][0]                        # Date format
    if len(dates) > 0:
        datesOrdered = dates == sorted(dates, reverse=True)
    else:
        noDates = True                                                                            # Dates Present
    if dtFormat == True:
        dateScore += 3
    if datesOrdered == True:
        dateScore += 1
    if noDates == False:
        dateScore += 6
    skill_ruler = EntityRuler(nlp, overwrite_ents=True).from_disk('./skill_patterns.jsonl')
    verb_ruler = EntityRuler(nlp, overwrite_ents=True).from_disk('./actionVerbs.jsonl')
    coms_ruler = EntityRuler(nlp, overwrite_ents=True).from_disk('./coms.jsonl')
    skill_ruler.name  = 'skillRuler'
    verb_ruler.name  = 'verbRuler'
    coms_ruler.name = 'comsRuler'
    nlp.add_pipe(skill_ruler, after='parser') 
    skillset_dict = create_skillset_dict([nlp(resume_text)])
    nlp.disable_pipes('skillRuler')
    nlp.add_pipe(verb_ruler, after='parser') 
    wordset_dict_verb = create_skillset_dict_verb([nlp(resume_text)])
    wordset_dict_sumr = create_skillset_dict_verb([nlp(' '.join(resume_raw_text.splitlines()[:16]))])
    nlp.disable_pipes('verbRuler')
    nlp.add_pipe(coms_ruler, after='parser') 
    wordset_dict_coms = create_skillset_dict_verb([nlp(resume_text)])
    # vacature_skillset = create_skill_set(nlp(resume_text))
    repetition = []
    singles = []
    for i in list(wordset_dict_verb[0]):
        if resume_text.lower().count(i) > 2:
            repetition.append({i: resume_text.lower().count(i)})
        elif resume_text.lower().count(i) == 1:
            singles.append(i)
    bzW = []
    for i in buzzWords:
        if resume_text.lower().count(i) > 0:
            bzW.append(i)
    resumeReadCorrectly = checkReadability(resume_raw_text)
    exp, _exp = checkExperience(resume_raw_text)
    edu, _edu = checkEducation(resume_raw_text)
    email, _email = checkEmail(resume_text)
    linkdn, _linkdn = checkLinkedin(resume_text)
    sumr = checkSummary(resume_raw_text)
    ref = checkReferees(resume_raw_text)
    obj = checkObjective(resume_raw_text)
    if exp == True:
        sectionsScore +=2
    if edu == True:
        sectionsScore +=1
    if email == True:
        sectionsScore +=2
    if ref == False:
        sectionsScore +=1
    if obj == False:
        sectionsScore +=1
    if linkdn == True:
        sectionsScore +=1
    if sumr == True  and len(wordset_dict_sumr[0]) >= 4:
        sectionsScore +=2
    if [10 if len(auxList) > 0 else 0][0] == 10:
        overallBrevity +=19
    if [len(auxList) if len(auxList) < 10 else 10][0] < 5:
        overallBrevity +=25
    if [len(auxList) if len(auxList) < 10 else 10][0] >= 5:
        overallBrevity +=69
    overallImpact = round([(len(auxList)/40)*100 if (len(auxList)/40)*100 <= 100 else 100.0][0])
    buzzWordScore = [math.ceil(10 - 2.5*len(bzW)) if math.ceil(10 - 2.5*len(bzW)) >= 0 else 0][0]
    overallSkill = round([(len(skillset_dict[0])/34)*100 if (len(skillset_dict[0])/34)*100 <= 100 else 100.0][0])
    if level.lower() == 'senior':
        overallScore = (overallImpact/145)*25 + (overallBrevity/145)*25 + (sectionsScore*10/145)*25 + (overallSkill/145)*25
    if level.lower() == 'mid':
        overallScore = (overallImpact/140)*25 + (overallBrevity/140)*25 + (sectionsScore*10/140)*25 + (overallSkill/140)*25
    if level.lower() == 'junior':
        overallScore = (overallImpact/135)*25 + (overallBrevity/135)*25 + (sectionsScore*10/135)*25 + (overallSkill/135)*25
      
    responseJson["overallScore"] = [math.ceil(overallScore) if overallScore < 100 else 100][0]
    responseJson["overalImpact"] = overallImpact
    responseJson["overallBrevity"] = sectionsScore*2 + buzzWordScore*2 + dateScore*2
    responseJson["overallStyle"] = sectionsScore*10
    responseJson["overallSkill"] = overallSkill
    responseJson["quantifyingImpactScore"] = [math.ceil((round(len(impactList)/len(auxList)*100)/60)*10) if round((round(len(impactList)/len(auxList)*100)/60)*10) < 10 else 10][0]
    responseJson["quantifyingImpactPercentage"] = round(len(impactList)/len(auxList)*100)
    responseJson["repetitionScore"] = math.ceil((len(singles)/len(wordset_dict_verb[0]))*10)
    responseJson["repeatedWords"] = repetition
    responseJson["resumeLength"] = 6*len(resume_raw_text.splitlines())
    if 6*len(resume_raw_text.splitlines()) >= 450 and 6*len(resume_raw_text.splitlines()) <= 650:
        responseJson["resumeLengthScore"] = 10
    elif 6*len(resume_raw_text.splitlines()) < 450 and 6*len(resume_raw_text.splitlines()) >= 300:
        responseJson["resumeLengthScore"] = 6
    elif 6*len(resume_raw_text.splitlines()) < 300:
        responseJson["resumeLengthScore"] = 2
    elif 6*len(resume_raw_text.splitlines()) > 650:
        responseJson["resumeLengthScore"] = 0
    responseJson["maxResumeLength"] = maxResumeLength
    responseJson["bulletsFound"] = [False if len(auxList) == 0 else True][0]
    responseJson["bulletUseScore"] = [10 if len(auxList) > 0 else 0][0]
    responseJson["bulletPointDepthScore"] = [len(auxList) if len(auxList) < 10 else 10][0]
    responseJson["numberOfBullets"] = len(auxList)
    responseJson["maxBulletPoints"] = maxBulletPoints
    responseJson["resumeReadCorrectly"] = resumeReadCorrectly
    responseJson["sectionsScore"] = sectionsScore
    responseJson["experiencePresent"] = exp
    responseJson["experienceFoundIn"] = _exp
    responseJson["educationPresent"] = edu
    responseJson["educationFoundIn"] = _edu
    responseJson["referenceSectionPresent"] = ref
    responseJson["objectivePresent"] = obj
    responseJson["linkedInProfilePresent"] = linkdn
    responseJson["LinkedInProfile"] = _linkdn
    responseJson["summaryRequired"] = summaryRequired
    responseJson["improveSummary"] = len(wordset_dict_sumr[0]) < 4
    responseJson["buzzWordsScore"] = buzzWordScore
    responseJson["buzzWords"] = bzW
    responseJson["datesScore"] = dateScore
    responseJson["datesFound"] = [False if noDates == True else True][0]
    responseJson["dateFormatCorrect"] = dtFormat
    responseJson["dateInconsistent"] = [True if datesOrdered == False else False][0]
    responseJson["communicationScore"] = round([(len(wordset_dict_coms[0])/5)*10 if (len(wordset_dict_coms[0])/5)*10 < 10 else 10][0])
    responseJson["communicationPercent"] = round([(len(wordset_dict_coms[0])/5)*100 if (len(wordset_dict_coms[0])/5)*100 < 100 else 100][0])
    responseJson["communicationWords"] = wordset_dict_coms

    
    
    print(responseJson)


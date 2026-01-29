from mjanalyzer_web import parse_tiles, _validate_counts
import re

FILENAME = "SimCat VS Dartrix VS MeowCaTS VS Rowlet (2025_05_03_17_29_56_3208)-(Rowlet(Win))_Win.txt"

Player = [[] for _ in range(4)]
abandonList = []

PlayerBank = ''#莊家人物
def getPlayerFromLoc(char):
    order = {'E':0, 'S':1, 'W':2, 'N':3}
    if PlayerBank == '':
        return -1
    if char == PlayerBank:
        return 0
    return (order[char] - order[PlayerBank]) % 4

def processAction(Step):
    actionStr = Step[2]
    try:
        if(actionStr == 'M'):#摸牌，進手排
            Player[getPlayerFromLoc(Step[1])].append(Step[3])
        if(actionStr == 'HD'):#打牌，捨手排 去牌池
            Player[getPlayerFromLoc(Step[1])].remove(Step[3])
            abandonList.append(Step[3])
        if(actionStr == 'MD'):#摸切
            pass
        if(actionStr == 'P'):#碰 捨對手排，進自己牌池(三排相同)
            abandonList.remove(Step[3])
            Player[getPlayerFromLoc(Step[1])].append(Step[3])
        if(actionStr == 'E' or actionStr == 'EM'):#吃 捨對手排，進自己牌池(連續)
            abandonList.remove(Step[4])
            Player[getPlayerFromLoc(Step[1])].append(Step[4])
            pass
        if(actionStr == 'EL'):#???
            pass
        if(actionStr == 'UG'):#吃 捨對手排，進自己牌池(連續)
            pass
        if(actionStr == 'H'):#???
            pass
    except:
        print('err')
        pass


Step = []
def processFile():
    with open(FILENAME, "r", encoding='utf-16-le') as f:
        for line in f:
            if re.match(r'\*\s*\d+\.', line):
                Step.append(line.replace(".", "").replace("* ", "").strip().split(' ')) #Step list
            if("SQRWALL" in line):
                river = line.replace("* SQRWALL ", "").split(' ')#River wall list
                k = 0
                for i in range(0, 64, 4):
                    for j in range(4):
                        Player[k].append(river[i+j])
                    if(k == 3):
                        k = 0
                    else:
                        k += 1

def strCard(cards):
    typeDict = {0:'花', 1:'萬', 2:'筒', 3:'條', 4:'字'}
    out = ""
    for card in cards:
        card = int(card)
        out +=  str(str(int(card/10%10)) + typeDict[int(card/100)] + '(' + str(card%10) +') ')
    return out

if __name__ == "__main__":
    processFile()
    PlayerBank = Step[0][1]
    inputIndex = int(input('輸入模擬的步驟:'))
    if(inputIndex > len(Step)):
        print("超出模擬步驟範圍")
        exit()
    for i in range(inputIndex):
        processAction(Step[i])
        for j in range(4):
            print("北:" + strCard(sorted(Player[getPlayerFromLoc('N')])) + '\n')
            print("東:" + strCard(sorted(Player[getPlayerFromLoc('E')])) + '\n')
            print("南:" + strCard(sorted(Player[getPlayerFromLoc('S')])) + '\n')
            print("西:" + strCard(sorted(Player[getPlayerFromLoc('W')])) + '\n')
            print("池:" + strCard(abandonList))
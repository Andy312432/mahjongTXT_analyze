from mjanalyzer_web import parse_tiles, _validate_counts
import re

FILENAME = "SimCat VS Dartrix VS MeowCaTS VS Rowlet (2025_05_03_17_29_56_3208)-(Rowlet(Win))_Win.txt"

Player = [[] for _ in range(4)]

PlayerBank = ''#莊家人物
def getPlayerFromLoc(char):
    order = {'E':0, 'S':1, 'W':2, 'N':3}
    if PlayerBank == '':
        return -1
    if char == PlayerBank:
        return 0
    return (order[char] - order[PlayerBank]) % 4

def processAction(actionStr):
    if(actionStr.startswith('M')):#摸牌，牌河進手排
    if(actionStr.startswith('HD')):#打牌，將手排捨 去牌池
    if(actionStr.startswith('MD')):#摸牌，牌河進手排
   
    if(actionStr.startswith('MD'))


Step = []
def processFile():
    Step = []
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
    PlayerBank = Step[0][1]

if __name__ == "__main__":
    processFile()
    inputIndex = int(input('輸入模擬的步驟:'))
    if(inputIndex > len(Step)):
        print("超出模擬步驟範圍")
        exit()
    for i in range(inputIndex):
        PlayerIndex = getPlayerFromLoc(Step[i][1])
        if Step[i][]
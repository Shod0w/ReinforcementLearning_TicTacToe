import numpy as np
import pickle

BOARD_ROWS = 3
BOARD_COLS = 3

class State:

    def __init__(self, p1, p2):
        self.board = np.zeros((BOARD_ROWS, BOARD_COLS))
        self.p1 = p1
        self.p2 = p2
        self.isEnd = False
        self.boardHash = None
        self.playerSymbol = 1
    

    def getHash(self):
        self.boardHash = str(self.board.reshape(BOARD_COLS*BOARD_ROWS))
        return self.boardHash


    def isWinner(self):

        #row
        for i in range(BOARD_ROWS):
            if sum(self.board[i,:]) == 3:
                self.isEnd = True
                return 1
            if sum(self.board[i,:]) == -3:
                self.isEnd = True
                return -1

        #column
        for i in range(BOARD_COLS):
            if sum(self.board[:,i]) == 3:
                self.isEnd = True
                return 1
            if sum(self.board[:,i]) == -3:
                self.isEnd = True   
                return -1

        #diagonal
        diagSum1 = sum([self.board[i,i] for i in range(BOARD_COLS)])
        diagSum2 = sum([self.board[i, BOARD_COLS - i - 1] for i in range(BOARD_COLS)])
        diagSum = max(abs(diagSum1), abs(diagSum2))
        if diagSum == 3:
            self.isEnd = True
            if diagSum1 == 3 or diagSum2 == 3:
                return 1
            else:
                return -1
        
        #tie
        #no available option
        if len(self.avaialablePositions()) == 0:
            self.isEnd = True
            return 0
        #not over
        self.isEnd = False
        return None


    def avaialablePositions(self):
        pos = []
        for i in range(BOARD_ROWS):
            for j in range(BOARD_COLS):
                if self.board[i,j] == 0:
                    pos.append((i,j))
        return pos


    def updateState(self,position):
        self.board[position] = self.playerSymbol
        #switch player
        self.playerSymbol = -1 if  self.playerSymbol == 1 else 1


    def Reward(self):
        result = self.isWinner()
        #backprop reward
        if result == 1:
            self.p1.feedReward(1)
            self.p2.feedReward(0)
        elif result == -1:
            self.p1.feedReward(0)
            self.p2.feedReward(1)
        else:
            self.p1.feedReward(0.1)
            self.p2.feedReward(0.5)


    def reset(self):
        self.board = np.zeros((BOARD_ROWS, BOARD_COLS))
        self.boardHash = None
        self.isEnd = False
        self.playerSymbol = 1


    #computer vs computer
    def play(self, rounds=100):
        for i in range(rounds):
            if i % 1000 == 0:
                print("Rounds {}".format(i))
            while not self.isEnd:
                #P1
                pos = self.avaialablePositions()
                p1Action = self.p1.chooseAction(pos, self.board, self.playerSymbol)
                #action and board update
                self.updateState(p1Action)
                board_hash = self.getHash()
                self.p1.addState(board_hash)

                win = self.isWinner()
                if win is not None:


                    self.Reward()
                    self.p1.reset()
                    self.p2.reset()
                    self.reset()
                    break
                
                else:
                    #P2
                    pos = self.avaialablePositions()
                    p2Action = self.p2.chooseAction(pos, self.board, self.playerSymbol)
                    self.updateState(p2Action)
                    board_hash = self.getHash()
                    self.p2.addState(board_hash)

                    win = self.isWinner()
                    if win is not None:


                        self.Reward()
                        self.p1.reset()
                        self.p2.reset()
                        self.reset()
                        break

    #human vs computer
    def play1(self):
        while not self.isEnd:
            #P1
            pos = self.avaialablePositions()
            p1Action = self.p1.chooseAction(pos, self.board, self.playerSymbol)
            #action and update
            self.updateState(p1Action)
            self.showBoard()
            #check board status
            win = self.isWinner()
            if win is not None:
                if win == 1 :
                    print(self.p1.name, " Wins.")
                else:
                    print("Game Tied")
                self.reset()
                break
            
            else:
                #P2
                pos = self.avaialablePositions()
                p2Action = self.p2.chooseAction(pos)
                self.updateState(p2Action)
                self.showBoard()
                win = self.isWinner()
                if win is not None:
                    if win == -1 :
                        print(self.p2.name, " Wins.")
                    else:
                        print("Game Tied")
                    self.reset()
                    break
    

    def showBoard(self):
        #P1 is X and P2 is O
        for i in range(0,BOARD_ROWS):
            print('-------------')
            out = '| '
            for j in range(0, BOARD_COLS):
                if self.board[i,j] == 1:
                    mark = 'X'
                if self.board[i,j] == -1:
                    mark = 'O'
                if self.board[i,j] == 0:
                    mark = ' '
                out += mark + ' | '
            print(out)
            print('-------------')



class Player:
    def __init__(self, name, exp_rate=0.3):
        self.name = name
        self.states = []
        self.lr = 0.2
        self.exp_rate = exp_rate
        self.decay_gamma = 0.9
        self.statesValue = {}
    

    def getHash(self, board):
        boardHash = str(board.reshape(BOARD_COLS * BOARD_ROWS))
        return boardHash

    
    def chooseAction(self, pos, currBoard, symbol):
        if np.random.uniform(0,1) <= self.exp_rate:
            #random action
            idx = np.random.choice(len(pos))
            action = pos[idx]
        else:
            valMax = -999
            for p in pos:
                nextBoard = currBoard.copy()
                nextBoard[p] = symbol
                nextBoardHash = self.getHash(nextBoard)
                val = 0 if self.statesValue.get(nextBoardHash) is None else self.statesValue.get(nextBoardHash)

                if val >= valMax:
                    valMax = val
                    action = p


        return action


    def addState(self, state):
        self.states.append(state)


    def feedReward(self, reward):
        for st in reversed(self.states):
            if self.statesValue.get(st) is None:
                self.statesValue[st] = 0
            self.statesValue[st] += self.lr * (self.decay_gamma * reward - self.statesValue[st])
            reward = self.statesValue[st]
    

    def reset(self):
        self.states = []

    
    def savePolicy(self):
        forw = open('policy_' + str(self.name), 'wb')
        pickle.dump(self.statesValue, forw)
        forw.close()

    
    def loadPolicy(self, file):
        fr = open(file, 'rb')
        self.statesValue = pickle.load(fr)
        fr.close()



class HumanP:
    
    def __init__(self, name):
        self.name = name
    
    def chooseAction(self, pos):
        while True:
            row = int(input("Action Row: "))
            col = int(input("Acion Column: "))
            action = (row, col)
            if action in pos:
                return action


    def addState(self, state):
        pass
    

    def feedReward(self, reward):
        pass
    

    def reset(self):
        pass



if __name__ == "__main__":
    #train
    p1 = Player("p1")
    p2 = Player("p2")

    st = State(p1,p2)
    print("---Training---")
    st.play(50000)
    p1.savePolicy()
    p2.savePolicy()

    #vsHuman
    p1 = Player("computer", exp_rate=0)
    
    p2 = HumanP("Aayush")

    st = State(p1, p2)
    st.play1()
    
    p1 = Player("computer", exp_rate=0)
    p1.loadPolicy("policy_p1")
    
    p2 = HumanP("Aayush")
    print("---After using trained data---")
    st = State(p1, p2)
    st.play1()






    

    


    

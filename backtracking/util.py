class Stack:
    stack: list[int]
    
    def __init__(self, n=1):
        self.stack: list[int] = [n,]
    
    def append(self, n: int) -> None:
        self.stack.append(n)
        
    def mut(self, n: int) -> None:
        self.stack[-1] = n
    
    def get(self) -> int:
        return self.stack[-1]
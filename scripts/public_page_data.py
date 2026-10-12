"""Read the data-only subset of a public page's serialized state. Never executes JS."""
import json,re
TOKEN=re.compile(r'\s*(?:("(?:\\.|[^"\\])*")|(\$R\[\d+\])|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|([A-Za-z_$][\w$]*)|(.))',re.S)
class Reader:
 def __init__(self,text,refs=None):
  self.tokens=[next(x for x in m.groups() if x is not None) for m in TOKEN.finditer(text)];self.i=0;self.refs=refs if refs is not None else {}
 def pop(self):
  t=self.tokens[self.i];self.i+=1;return t
 def peek(self):return self.tokens[self.i] if self.i<len(self.tokens) else ''
 def value(self):
  t=self.pop()
  if t.startswith('$R['):
   if self.peek()=='=':
    self.pop();v=self.value();self.refs[t]=v;return v
   if t not in self.refs:raise ValueError('Unresolved data reference '+t)
   return self.refs[t]
  if t=='{':
   d={}
   while self.peek()!='}':
    k=self.pop();k=json.loads(k) if k.startswith('"') else k
    if self.pop()!=':':raise ValueError('Invalid object')
    d[k]=self.value()
    if self.peek()==',':self.pop()
    elif self.peek()!='}':raise ValueError('Invalid object separator')
   self.pop();return d
  if t=='[':
   a=[]
   while self.peek()!=']':
    a.append(self.value())
    if self.peek()==',':self.pop()
    elif self.peek()!=']':raise ValueError('Invalid array separator')
   self.pop();return a
  if t=='!':
   n=self.pop()
   if n not in ('0','1'):raise ValueError('Unsupported boolean')
   return n=='0'
  if t.startswith('"'):return json.loads(t)
  if t=='null':return None
  if t in ('true','false'):return t=='true'
  if re.fullmatch(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?',t):return json.loads(t)
  raise ValueError('Unsupported public-data token '+t)
def object_after(text,start,refs=None):
 # Bound the object without treating braces inside quoted strings as structure.
 depth=0;quoted=False;escape=False
 for i in range(start,len(text)):
  c=text[i]
  if quoted:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c=='"':quoted=False
  elif c=='"':quoted=True
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return Reader(text[start:i+1],refs).value()
 raise ValueError('Truncated data object')

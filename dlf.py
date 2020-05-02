import asyncio, os
from aiohttp import ClientSession
from tqdm import tqdm
# proxy = 'http://your_user:your_password@your_proxy_url:your_proxy_port'
async def _dl(url, session, proxy, start, end, file, block_size, pbar):
    if start > end:
        return
    async with session.get(url, headers={'Range': f"bytes={start}-{end}"}, proxy=proxy) as req:
        #print(req.headers)
        chunk = await req.content.read(block_size)
        while chunk:
            pbar.update(file.write(chunk))
            chunk = await req.content.read(block_size)
    file.close()

def _len(Response):
    return int(Response.headers.get('content-length',-1))
def _path(name):
    p =  os.path.join(os.getcwd(),name)
    if not os.path.exists(p):
        os.mkdir(p)
    return p
def _fs(name, id):
    p = os.path.join(_path(name),str(id))
    return int(os.path.exists(p) and os.path.getsize(p))   
def _BytesIO(name, id):
    return open(os.path.join(_path(name),str(id)),'ab')
def _listdir(name):
    p = _path(name)
    return [os.path.join(p,f) for f in sorted(os.listdir(p), key = int)]

def _task_one(id, start, end, name, pbar):
    s = _fs(name, id)
    start += s
    pbar.update(s)
    if start <= end:
        file = _BytesIO(name, id)
    else:
        file = None
    return (start,end,file)

def _task_split(size, task_size, name, pbar):
    t = [(id,s,s+task_size-1) for id,s in enumerate(range(0,size,task_size))]
    td = t[-1]
    t[-1] = (td[0],td[1],size-1)
    return [_task_one(id,s,e,name, pbar) for id,s,e in t]

class downloader(object):
    def __init__(self, url, block_size=1024, task_size=1048576, name='Downloading'):
        if url and len(url[0])==3:
            self.url = url
        else:
            raise ValueError('URL must include [(url, headers, proxy)]')
        self.block_size = block_size
        self.task_size = task_size
        self.name = name
        self._len = None
        self.loop = asyncio.get_event_loop()
    async def len(self, session):
        if not self._len:
            async with session.get(self.url[0][0], proxy=self.url[0][2]) as r:
                self._len = _len(r)
        return self._len
    async def _next(self, s, u):
        while self._task:
            t = self._task.pop()
            await _dl(u[0],s,u[2],t[0],t[1],t[2],self.block_size,self._pbar)
    async def fetch(self):
        se = [ClientSession(headers=h) for u,h,p in self.url]
        size = await self.len(se[0])
        self._pbar = tqdm(total=size,initial=0,unit='B',unit_scale=True, desc=self.name)
        self._task = _task_split(size, self.task_size, self.name, self._pbar)
        await asyncio.wait([self._next(s,u) for s,u in zip(se, self.url)])
        self._pbar.close()
        await asyncio.wait([s.close() for s in se])
        return size
    def start(self): 
        self.loop.run_until_complete(self.fetch())
    def close(self):
        self.loop.close()
    def save(self, file=None):
        if not file:
            file = open(_path(self.name)+'.data','wb')
        for p in tqdm(_listdir(self.name)):
            with open(p,'rb') as f:
                file.write(f.read())
        file.close()
    def clear(self):
        for p in tqdm(_listdir(self.name)):
            os.remove(p)
        self.close()


if __name__ == "__main__":
    u1 = r'https://vdept.bdstatic.com/474457754e33544c664262346157315a/327331714a794373/c14148685ffa00554cdeaec06666672a7484885f3021a5ec53292cf7be931c6f1566ecf0cdf11e3dd4991df77360f688.mp4?auth_key=1588438914-0-0-af4de22d9f88094cdb27182c0932b023'
    headers1 = {
    "Referer": "https://haokan.baidu.com/v?vid=7775090863583036142&pd=bjh&fr=bjhauthor&type=video",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"
    }
    u2 = u1
    headers2 = headers1
    a = downloader([(u1,headers1,None),(u2,headers2,None)])
    a.start()
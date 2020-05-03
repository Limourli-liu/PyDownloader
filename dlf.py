import asyncio, os
from aiohttp import ClientSession
from tqdm import tqdm
ncols = 80
# proxy = 'http://your_user:your_password@your_proxy_url:your_proxy_port'
async def _dl(url, session, proxy, start, end, p, block_size, pbar):
    if start > end:
        return
    async with session.get(url, headers={'Range': f"bytes={start}-{end}"}, proxy=proxy) as req:
        #print(req.headers)
        chunk = await req.content.read(block_size)
        with _fopen(p) as file:
            while chunk:
                pbar.update(file.write(chunk))
                chunk = await req.content.read(block_size)

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
    return os.path.join(_path(name),str(id))
def _fopen(p):
    return open(p,'ab')
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
    def __init__(self, url, block_size=1024, task_size=1048576, name='Downloading', loop=None):
        if url and len(url[0])==3:
            self.url = url
        else:
            raise ValueError('URL must include [(url, headers, proxy)]')
        self.block_size = block_size
        self.task_size = task_size
        self.name = name
        self._len = None
        if loop:
            self.loop = loop
        else:
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
        self._pbar = tqdm(total=size,initial=0,unit='B',unit_scale=True, desc=self.name, ncols=ncols)
        self._task = _task_split(size, self.task_size, self.name, self._pbar)
        await asyncio.wait([self._next(s,u) for s,u in zip(se, self.url)])
        self._pbar.close()
        await asyncio.wait([s.close() for s in se])
        return size
    def start(self): 
        self.loop.run_until_complete(self.fetch())
    def close(self):
        self.loop.close()
    def save(self, file=None, Clear=True):
        if not file:
            file = open(_path(self.name)+'.data','wb')
        for p in tqdm(_listdir(self.name), ncols=ncols, desc=f'save {self.name}'):
            with open(p,'rb') as f:
                file.write(f.read())
        file.close()
        if Clear:
            self.clear()
    def clear(self):
        for p in tqdm(_listdir(self.name), ncols=ncols, desc=f'clear {self.name}'):
            os.remove(p)


if __name__ == "__main__":
    u1 = r'https://vdept.bdstatic.com/7a43666e6a3461324c38636c49685770/78616b46597a5834/e5d1ba41a50707c5555057714e97d98dce7b4175ed6a58d60be82e66be37dfeee1a92d5454c5e9bb2ac352ebf5f93bf8.mp4?auth_key=1588491316-0-0-9102ee51bf7d4e0483c7b1d33c16d576'
    headers1 = {
    "Accept": "*/*",
    "Accept-Encoding": "identity;q=1, *;q=0",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Host": "vdept.bdstatic.com",
    "Referer": "https://haokan.baidu.com/v?vid=17626321789640264935",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"
    }
    u2 = u1
    headers2 = headers1
    a = downloader([(u1,headers1,None),(u2,headers2,None)])#同一个url重复则可以起到模拟多线程下载的效果,重复2次为2个连接
    a.start()
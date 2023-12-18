import asyncio
import random

# async def sleep(time, index):
#     await asyncio.sleep(time)
#     print(f'{index} slept {time}')
#     return index

# async def main():
#     tasks = [asyncio.create_task(sleep(random.randint(0,10), i)) for i in range(10)]

#     for coro in asyncio.as_completed(tasks):
#         i = await coro
#         print(f'hello from {i}')
#     print('hello')

# asyncio.run(main())

try:
    
    raise Exception('hello')

except TypeError as e:
    print(e)
except Exception as e:
    print('pp')

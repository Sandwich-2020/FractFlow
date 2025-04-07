我希望更新一下我的接口，使得用户可以很容易地用。具体来说，调用时应该是： 

``` pseudocode
import fractalmcp
agent = fractalmcp.Agent()
config = agent.get_config()
config['deepseek']['api_key'] = 'your_api_key'
...
agent.set_config(config)

agent.add_tool(tool_path1)
agent.add_tool(tool_path2)
...

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ('exit', 'quit', 'bye'):
        break
        
    print("\nAgent: ", end="")
    result = await agent.process_query(user_input)
    print(result)

```

然后，我希望我的接口文件在FractalMCP/agent.py 中，我最终是希望把它封装成一个package，然后用户可以pip install FractalMCP 就可以使用。
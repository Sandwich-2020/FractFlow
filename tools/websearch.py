import requests
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, parse_qs
from mcp.server.fastmcp import FastMCP
from bs4 import BeautifulSoup

# 初始化MCP服务器
mcp = FastMCP("web_search_executor")

# ------------------------------------------------------------------------
# 网络工具函数
# ------------------------------------------------------------------------

def _get_user_agent() -> str:
    """返回通用的User-Agent头信息"""
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def _make_request(url: str, timeout: int = 15) -> requests.Response:
    """
    发送HTTP请求并返回响应
    
    Args:
        url: 请求的URL
        timeout: 超时时间（秒）
        
    Returns:
        requests.Response对象
    
    Raises:
        requests.exceptions.RequestException: 当请求失败时
    """
    headers = {"User-Agent": _get_user_agent()}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response

@mcp.tool()
async def web_browse(url: str, extract_type: str = "full_text") -> str:
    """
    获取并提取网页内容
    
    Args:
        url (str): 要浏览的网页URL
        extract_type (str, optional): 要提取的内容类型。可选值:
                                      "full_text" - 提取所有文本内容
                                      "title" - 仅提取页面标题
                                      "links" - 提取页面上所有链接
                                      "html" - 返回原始HTML
                                      默认为 "full_text"
        
    Returns:
        str: 根据extract_type提取的网页内容，或在URL无效或请求失败时返回错误信息
        
    Example:
        web_browse("https://www.example.com", extract_type="full_text")
    """
    try:
        # 检查URL是否有效
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return "无效URL。请提供完整URL，包括http://或https://"
        
        # 发送请求
        response = _make_request(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 根据extract_type提取内容
        if extract_type == "full_text":
            # 移除script和style元素
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator="\n", strip=True)
            return text
            
        elif extract_type == "title":
            title = soup.title.string if soup.title else "未找到标题"
            return title
            
        elif extract_type == "links":
            links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    links.append(f"{link.text.strip()} - {href}")
            return "\n".join(links) if links else "未找到链接"
            
        elif extract_type == "html":
            return response.text
            
        else:
            return f"无效的extract_type: {extract_type}。有效选项: full_text, title, links, html"
            
    except requests.exceptions.RequestException as e:
        return f"获取URL失败: {str(e)}"
    except Exception as e:
        return f"发生错误: {str(e)}"

@mcp.tool()
async def web_search(query: str, search_engine: str = "duckduckgo", num_results: int = 5) -> str:
    """
    执行网络搜索并返回相关结果
    
    Args:
        query (str): 要搜索的关键词或短语
        search_engine (str, optional): 要使用的搜索引擎
                                      可选值: "duckduckgo", "bing", "google"
                                      默认为 "duckduckgo"
        num_results (int, optional): 要返回的结果数量，默认为5个
        
    Returns:
        str: 包含标题、链接和描述的搜索结果，或在搜索失败时返回错误信息
        
    Example:
        web_search("Python 编程教程", search_engine="duckduckgo", num_results=3)
    """
    try:
        # 验证num_results参数
        if num_results <= 0:
            return "结果数量必须大于0"
        
        if num_results > 20:
            num_results = 20
            
        search_engine = search_engine.lower()
        
        if search_engine == "duckduckgo":
            return await _search_duckduckgo(query, num_results)
        elif search_engine == "bing":
            return await _search_bing(query, num_results)
        elif search_engine == "google":
            return await _search_google(query, num_results)
        else:
            return f"不支持的搜索引擎: {search_engine}。支持的选项: duckduckgo, bing, google"
            
    except requests.exceptions.RequestException as e:
        return f"搜索请求失败: {str(e)}"
    except Exception as e:
        return f"执行搜索时发生错误: {str(e)}"

async def _search_duckduckgo(query: str, num_results: int) -> str:
    """
    使用DuckDuckGo搜索引擎执行搜索
    
    Args:
        query: 搜索查询
        num_results: 要返回的结果数量
        
    Returns:
        格式化的搜索结果字符串
    """
    url = f"https://html.duckduckgo.com/html/?q={query}"
    response = _make_request(url, timeout=15)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    # 解析DuckDuckGo的搜索结果
    for result in soup.select('.result')[:num_results]:
        title_elem = result.select_one('.result__title')
        if not title_elem:
            continue
            
        title = title_elem.get_text(strip=True)
        link_elem = title_elem.select_one('a')
        link = link_elem.get('href') if link_elem else "链接未找到"
        
        # 处理DuckDuckGo的重定向链接
        if link.startswith('/'):
            # 这是DuckDuckGo的重定向链接，尝试提取真实URL
            try:
                parsed = parse_qs(link.split('?', 1)[1])
                if 'uddg' in parsed:
                    link = parsed['uddg'][0]
            except:
                pass
        
        snippet_elem = result.select_one('.result__snippet')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else "没有可用的描述"
        
        results.append(f"📌 {title}\n🔗 {link}\n📄 {snippet}\n")
    
    if not results:
        return f"在DuckDuckGo上没有找到与'{query}'相关的结果"
        
    return f"🔍 '{query}'的搜索结果:\n\n" + "\n".join(results)

async def _search_bing(query: str, num_results: int) -> str:
    """
    使用Bing搜索引擎执行搜索
    
    Args:
        query: 搜索查询
        num_results: 要返回的结果数量
        
    Returns:
        格式化的搜索结果字符串
    """
    url = f"https://www.bing.com/search?q={query}"
    response = _make_request(url, timeout=15)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    # 解析Bing的搜索结果
    for result in soup.select('.b_algo')[:num_results]:
        title_elem = result.select_one('h2')
        if not title_elem:
            continue
            
        title = title_elem.get_text(strip=True)
        link_elem = title_elem.select_one('a')
        link = link_elem.get('href') if link_elem else "链接未找到"
        
        snippet_elem = result.select_one('.b_caption p')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else "没有可用的描述"
        
        results.append(f"📌 {title}\n🔗 {link}\n📄 {snippet}\n")
    
    if not results:
        return f"在Bing上没有找到与'{query}'相关的结果"
        
    return f"🔍 '{query}'的搜索结果:\n\n" + "\n".join(results)

async def _search_google(query: str, num_results: int) -> str:
    """
    使用Google搜索引擎执行搜索
    
    Args:
        query: 搜索查询
        num_results: 要返回的结果数量
        
    Returns:
        格式化的搜索结果字符串
    """
    url = f"https://www.google.com/search?q={query}&num={min(num_results, 10)}"
    response = _make_request(url, timeout=15)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    # 解析Google的搜索结果
    # Google结构可能经常变化，这里使用一种常见的选择器
    for result in soup.select('div.g')[:num_results]:
        title_elem = result.select_one('h3')
        if not title_elem:
            continue
            
        title = title_elem.get_text(strip=True)
        
        link_elem = result.select_one('a')
        link = link_elem.get('href') if link_elem else "链接未找到"
        if link.startswith('/url?'):
            try:
                parsed = parse_qs(link.split('?', 1)[1])
                if 'q' in parsed:
                    link = parsed['q'][0]
            except:
                pass
        
        snippet_elem = result.select_one('div.VwiC3b')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else "没有可用的描述"
        
        results.append(f"📌 {title}\n🔗 {link}\n📄 {snippet}\n")
    
    if not results:
        return f"在Google上没有找到与'{query}'相关的结果"
        
    return f"🔍 '{query}'的搜索结果:\n\n" + "\n".join(results)

# 主入口
if __name__ == "__main__":
    mcp.run(transport="stdio")

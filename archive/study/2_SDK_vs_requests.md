# 공식 SDK(Software Development Kit)

공식 SDK(Software Development Kit)란 AI 서비스를 제공하는 기업(예: Google, OpenAI 등)이 개발자들이 자사 AI를 쉽게 쓸 수 있도록 직접 만들어서 배포한 도구 모음(라이브러리)을 말합니다.

개발 언어(Python, JavaScript 등)에 맞춰 미리 기능을 함수로 만들어 두었기 때문에, 복잡한 통신 코드를 짤 필요 없이 몇 줄의 명령어만으로 AI를 작동시킬 수 있습니다.

## requests 직접 호출과의 차이점

* 공식 SDK 사용 시 (추천):

보안 인증, 데이터 형식 변환, 오류 예외 처리 등이 이미 내부적으로 구현되어 있습니다.

```python
# 예시: 공식 SDK를 사용하는 경우 (매우 간결함)
import google.genai as genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="안녕?",
)
print(response.text)
```

* `requests` 직접 호출 시:

공식 SDK가 지원하지 않는 언어를 쓰거나, 가벼운 환경을 구축할 때 씁니다.
웹 통신 규격(주소, 헤더, 데이터 형식)을 개발자가 하나하나 직접 세팅해야 해서 코드가 길어지고 실수가 생기기 쉽습니다.

```python
# 예시: requests로 직접 API 주소에 요청하는 경우 (복잡함)
import requests

url = "https://googleapis.com"
headers = {"Content-Type": "application/json"}
data = {"contents": [{"parts": [{"text": "안녕?"}]}]}

response = requests.post(url, headers=headers, json=data)
print(response.json()["candidates"][0]["content"]["parts"][0]["text"])
```

## 공식 SDK의 주요 장점

* 쉬운 코드: 복잡한 API 주소(URL)나 JSON 구조를 몰라도 함수 호출 한 번으로 해결됩니다.
* 유지보수: AI 기능이 업데이트되면 SDK 버전만 업데이트하면 되므로 관리가 편합니다.
* 보안 및 안정성: 연결이 끊겼을 때 재시도하는 기능이나 보안 인증 처리가 안전하게 설계되어 있습니다.

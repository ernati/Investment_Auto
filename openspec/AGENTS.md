# AGENTS.md
 
## 언어 정책
 
- **모든 사용자에게 보이는 출력과 프로젝트 파일에 작성되는 Markdown 산문은 반드시 한국어로 작성해야 합니다.**
- 코드, 명령어, 파일 경로, API 이름 등 기술적 식별자는 원래 언어(영어)를 유지합니다.
- 출처: `.github/copilot-instructions.md`
 
---
 
## OpenSpec 워크플로
 
이 프로젝트는 **OpenSpec** 스펙 주도 개발을 사용합니다.
 
- `openspec/specs/` — 컴포넌트별 정식 스펙 (신뢰할 수 있는 소스)
- `openspec/changes/` — 진행 중인 change (proposal, design, tasks)
- `openspec/changes/archive/` — 완료된 change 아카이브
 
**슬래시 명령어** (`.opencode/command/` 경유):
 
| 명령어 | 역할 |
|---|---|
| `/opsx:new` | 새 change 시작, 아티팩트 단계별 생성 |
| `/opsx:propose` | opsx:new + opsx:continue |
| `/opsx:explore` | 요구사항 심층조사/정리 |
| `/opsx:apply` | 진행 중인 change의 tasks 구현 |
| `/opsx:continue` | 진행 중인 change 아티팩트 작성 재개 |
| `/opsx:verify` | 구현이 change 아티팩트와 일치하는지 검증 |
| `/opsx:archive` | change를 동기화하고 아카이브 |
| `/opsx:sync` | change의 스펙을 정식 스펙으로 병합 (수동으로 쓰일 일 없음) |
 
---
 
## 코딩 스타일
 
없음.
 
---
 
## 프롬프트
 
없음.
 
---
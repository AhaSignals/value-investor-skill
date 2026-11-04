# value-investor-skill

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md)

## この株は、今の価格に見合うのか？

企業の事業を調べ、評価の前提を確かめ、株価を正当化するには何が必要かを考える。**[AhaSignals](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=ja_methodology)** が公開する、AI アシスタント向けの投資リサーチ用スキルです。

[ブラウザーでデモを試す](https://ahasignals.com/value-investor-skill/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=ja_demo) · [評価が変わる例](docs/demo.md) · [MIT ライセンス](LICENSE)

**1つのスキルに8つの調査ワークフロー。架空の事例3件、デモ図4点、6つのチャット入口、7言語のガイド、HTML・Markdown・JSONの出力。**

### 財務諸表・過去のPER・価格推移を調べる

| 調査 | 確認できること |
| --- | --- |
| 財務諸表 | 年次売上成長率、利益率、営業キャッシュフローと利益の比率、設備投資後の資金、純有利子負債、株式数の増加 |
| 過去のPER | 過去の月次平均・中央値・順位。赤字や比較できない事業環境では比較を保留 |
| 価格の背景 | 日足OHLC、50・200観測値の移動平均、下落率。反発予測ではありません |

従来の事業分析、評価シナリオ、株価の前提、反証、証拠の更新と合わせて8つのワークフローです。架空の製造企業はPER10倍、過去の中央値20倍。しかし純利益1,500万に対し営業キャッシュフロー500万、設備投資800万で、差額はマイナス300万です。純有利子負債と株式数も増えています。低PERの理由を調べる出発点になります。

> [企業名]の年次報告書を調べ、利益が現金になっているか、低PERが事業の変化を反映しているか説明してください。日足は背景情報に使い、反証と次に読むべき資料を示してください。出典と日付を添え、不明な値は埋めないでください。

```bash
python3 scripts/investor.py scan-demo --out output/value-trap
```

`output/value-trap/scan.html`で3つの図と調査項目を確認できます。実データはアシスタントが財務資料や利用可能な価格データから整理し、`scan`または`scan-batch`へ渡します。全市場の自動取得や任意PDFの自動解析ではありません。[入力仕様](references/scan-input.md)・[平均回帰の検証方法](references/scanning.md)。過去の平均PERは適正価値ではなく、平均回帰には事業上の理由と反証可能な仮説が必要です。銀行・保険・不動産投資信託には別の会計指標が必要です。

![架空の40ドル株：同じ価格でも、必要な前提は異なる](assets/demo.svg)

### Claude・GPT・DeepSeek・Grok・Gemini・Kimi で始める

Claude、ChatGPT、DeepSeek、Grok、Gemini、Kimi のチャットでは、[コピー用の研究指示](prompts/START_HERE.md)を貼り付け、日本語で回答するよう依頼できます。ターミナルは不要です。Claude Code はプラグイン、Codex はローカルスキルとして利用できます。[アプリ別の導入手順](docs/hosts.md)。実行できるツールは利用するアプリによって異なります。

### 1分で試す

Python 3.9 以降が必要です。この**架空のオフラインデモ**には、pip パッケージ、API キー、有料の市場データ、AI モデルの呼び出しは不要です。

```bash
git clone https://github.com/AhaSignals/value-investor-skill.git
cd value-investor-skill
python3 scripts/investor.py demo --out output/demo
```

`output/demo/before/research.html` と `output/demo/after/research.html` を開いて比較してください。Windows では `python3` の代わりに `py -3` を使えます。再実行時は新しい出力先を指定してください。既存の研究記録は上書きしません。

### スキルをインストール

```bash
python3 scripts/install.py --host codex
# Claude Code:
python3 scripts/install.py --host claude
```

アシスタントのスキルを再読み込みして、次のように依頼します。

> value-investor-skill を使い、この企業を一次資料から調べてください。現在の株価が成立するための前提、それを支える証拠、見方を変える反証を日本語で説明してください。不足するデータは推測で埋めないでください。

アシスタントには資料へのアクセス、または利用者が提供する文書が必要です。AI ホストやデータ提供元の費用・利用条件は別途適用されます。インストーラーは既存のスキルを上書きしません。

### 40ドルの株価から、何が分かる？

以下は架空の現在価値の仮定です。

| 有利なシナリオ | 不利なシナリオ | 40ドルと一致する有利な側の重み |
| ---: | ---: | ---: |
| 80ドル | 20ドル | 33.3% |
| 60ドル | 20ドル | 50.0% |

それぞれ別の2状態の計算です。**この重みは、出来事の成功確率でも信頼区間でもありません。** 80ドルと60ドルのどちらを裏づける資料があるかが、次の調査課題です。

デモで発売時期の根拠を取り下げると、それに依存する評価は `NEEDS_REVIEW` となり、新しい数値の表示を保留します。元の研究と無関係なシナリオは残ります。

### AhaSignals の研究手順

- 株価から逆算して事業価値を作らず、シナリオの経済条件と市場価格を分けます。
- 公開日時と実際に観測した日時を区別し、資料と評価の依存関係を記録します。
- 現金、負債、将来費用、資金調達と株式希薄化を1株当たり価値に反映します。
- 修正は履歴に追加し、過去の判断を保持します。
- 検証済みの確率を推定できない場合は `NOT_ESTIMATED`、投資判断の提示は `NO_QUOTE` とします。

この版はシナリオ計算と研究記録のためのものです。自動の全市場分析、検証済みの予測確率、個人向け投資助言、取引執行は提供しません。資料の日付は申告値であり、内容の真実性を自動認証するものではありません。

### 続けて調べる

[入力仕様](references/input-contract.md) · [研究手順](references/research-protocol.md) · [AhaSignals の資料と修正履歴](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=ja_methodology) · [翻訳の修正を報告](https://github.com/AhaSignals/value-investor-skill/issues)

この日本語版は導入ガイドです。CLI、生成レポート、詳細仕様は英語で、AI の回答言語は利用するホストによります。翻訳のレビューを歓迎します。

AhaSignals は独立した研究発行者です。研究・教育目的であり、投資や売買の助言ではありません。第三者名は出典・互換性の説明に限り、提携や推奨を意味しません。コードと独自の架空データは MIT ライセンスです。第三者資料の再配布権は含みません。

# Amazon Ads 用語集（公式出典つき・2026-09-09 制定）

`TERMS_AMAZON.md`（カテゴリー・商品の単位／順位・シェア／価格）の**広告側**の対。
**出典はすべて Amazon Ads 公式サイトの日本語ガイド**（`https://advertising.amazon.com/ja-jp/library/guides/…`）。
取得日 = **2026-09-09**。定義は公式の記述をそのまま引用し、5co 側で要約・言い換えをしていない。

> なぜ出典を付けるか: `TERMS_AMAZON.md` は「正式用語」を定めているが**根拠URLが無い**ため、
> 「本当に Amazon の表記か」を後から誰も確認できなかった。用語の正しさは**一次情報でしか確定しない**
> （CLAUDE.md「原本ファースト」）。本ファイルは行ごとに出典を持つ。
>
> 更新のしかた: 表記に迷ったら出典URLを開いて現物を確認する。ページの文言が変わっていたら、
> **引用と取得日を差し替える**（記憶や過去の資料で上書きしない）。

---

## 1. 広告プロダクト（正式名称）

**「広告」まで含めて正式名称**。「スポンサープロダクト」と切らない。略記（SP/SB/SD）は図中のみ可で、初出とスライド凡例で正式名称を示す。

| 正式用語 | 公式の定義（引用） | 出典 |
|---|---|---|
| **スポンサープロダクト広告** | 「Amazon内および一部のプレミアムアプリやウェブサイトで個別の出品商品を宣伝するための**クリック課金制（CPC）広告**です」 | [sponsored-products-best-practices](https://advertising.amazon.com/ja-jp/library/guides/sponsored-products-best-practices) |
| **スポンサーブランド広告** | 「広告主様に類似のブランドや商品を積極的に探しているお買い物中のお客様の注目を集め、露出度の高い掲載枠に表示するのに役立ちます」 | [sponsored-brands-what-to-know](https://advertising.amazon.com/ja-jp/library/guides/sponsored-brands-what-to-know) |
| **ディスプレイ広告** | 「画像、グラフィック、アニメーション、動画（OLVとも呼ばれます）などの視覚要素を使用して、ウェブサイト、アプリ、ソーシャルメディアプラットフォームで商品、サービス、ブランドを宣伝するデジタル広告フォーマットの一種です」 | [display-ads-guide](https://advertising.amazon.com/ja-jp/library/guides/display-ads-guide) |
| **Amazon DSP** | → 下記「デマンドサイドプラットフォーム（DSP）」。Amazon の DSP 製品名は **Amazon DSP**（DSP 単独で自社製品を指さない） | [demand-side-platform](https://advertising.amazon.com/ja-jp/library/guides/demand-side-platform) |

## 2. 費用と成果の指標

| 正式用語 | 公式の定義（引用） | 出典 |
|---|---|---|
| **広告費売上高比率（ACOS）** | 「広告費用と広告収益を測定する指標です。この指標を利用すると、ブランドの広告キャンペーン成功の度合いの判断に役立ちます」 | [acos-advertising-cost-of-sales](https://advertising.amazon.com/ja-jp/library/guides/acos-advertising-cost-of-sales) |
| **CPC（クリック単価）** | 「広告が獲得したクリック数に基づいて、ウェブサイトやソーシャルメディアに掲載された広告に対して広告主様が支払う金額を決定する指標です。CPCは、PPCまたはクリック報酬型とも呼ばれ」 | [cost-per-click](https://advertising.amazon.com/ja-jp/library/guides/cost-per-click) |
| **1,000回表示あたりの単価（CPM）** | 「マーケティングや広告で一般的に使用される価格設定モデルおよび指標です。インプレッション1,000回あたりの単価とも呼ばれるCPMは、広告が獲得する1,000インプレッションごとの広告費の合計を指します」 | [cost-per-mille](https://advertising.amazon.com/ja-jp/library/guides/cost-per-mille) |
| **ビューアビリティ** | 「人が閲覧した広告インプレッションをレポートにするデジタル広告指標です」 | [viewability](https://advertising.amazon.com/ja-jp/library/guides/viewability) |

## 3. ターゲティングと入札

| 正式用語 | 公式の定義（引用） | 出典 |
|---|---|---|
| **ターゲティング** | 「広告を表示する際のコンテキストを設定する方法です」 | [targeting-with-sponsored-products](https://advertising.amazon.com/ja-jp/library/guides/targeting-with-sponsored-products) |
| **キーワードターゲティング** | 「広告コピーに含まれる特定の単語を使用して、検索エンジンを通じて関連するオーディエンスにリーチする方法です」 | [keyword-targeting](https://advertising.amazon.com/ja-jp/library/guides/keyword-targeting) |
| **商品ターゲティング** | 「広告対象商品と関連性の高い特定の商品、カテゴリー、ブランド、その他の商品の機能をターゲットに設定することができる、マニュアルターゲティングの一種です」 | [targeting-with-sponsored-products](https://advertising.amazon.com/ja-jp/library/guides/targeting-with-sponsored-products) |
| **マッチタイプ**：**完全一致** / **フレーズ一致** / **部分一致** | 「完全一致では、お買い物中のお客様がキーワードを広告主様が入力したとおりに検索した場合にのみ広告が表示されます」（3種のマッチタイプはキャンペーンまたは広告グループレベルで適用） | [keyword-targeting](https://advertising.amazon.com/ja-jp/library/guides/keyword-targeting) |
| **除外キーワードターゲティング** / **除外商品ターゲティング** | 広告コンソールのキャンペーン作成時、または「除外キーワード」タブから追加する（公式の設定名） | [targeting-with-sponsored-products](https://advertising.amazon.com/ja-jp/library/guides/targeting-with-sponsored-products) |
| **動的な入札 - アップとダウン** | スポンサープロダクト広告の入札戦略の1つ（公式の設定名。「自動入札」「動的入札」と略さない） | [dynamic-bidding-sponsored-products](https://advertising.amazon.com/ja-jp/library/guides/dynamic-bidding-sponsored-products) |
| **リマーケティング** | 「以前にWebサイトにアクセスしたことのあるオーディエンスやソーシャルメディアコンテンツを利用したことがあるオーディエンスをターゲットに設定して広告を配信できるようにするマーケティング方法です」 | [remarketing](https://advertising.amazon.com/ja-jp/library/guides/remarketing) |
| **フリークエンシーキャップ** | 「特定の期間に同じユーザーに広告が表示される回数を制限する手法です」 | [frequency-capping](https://advertising.amazon.com/ja-jp/library/guides/frequency-capping) |

## 4. 配信の仕組み（アドテック）

| 正式用語 | 公式の定義（引用） | 出典 |
|---|---|---|
| **デマンドサイドプラットフォーム（DSP）** | 「広告主様が複数のアドエクスチェンジでデジタル広告在庫をリアルタイムで買い付けできるようにするツールです」 | [demand-side-platform](https://advertising.amazon.com/ja-jp/library/guides/demand-side-platform) |
| **サプライサイドプラットフォーム（SSP）** | 「セルサイドプラットフォームまたはSSPとも呼ばれ、インプレッションに基づいて、ウェブサイトやアプリ上の広告スペースの販売促進をサポートするために使用されるテクノロジーです」 | [supply-side-platform](https://advertising.amazon.com/ja-jp/library/guides/supply-side-platform) |
| **リアルタイム入札（RTB）** | 「プログラマティック広告の施策で、通常はインプレッションごとに広告在庫をリアルタイムのオークションで売買します」 | [real-time-bidding](https://advertising.amazon.com/ja-jp/library/guides/real-time-bidding) |
| **広告インベントリ** | 「購入可能な広告スペースのことです」 | [ad-inventory](https://advertising.amazon.com/ja-jp/library/guides/ad-inventory) |
| **Amazon Marketing Cloud（AMC）** | 「キャンペーンをサポートする一連のマーケティングツールとサービスです」 | [amazon-marketing-cloud](https://advertising.amazon.com/ja-jp/library/guides/amazon-marketing-cloud) |

## 5. 市場規模とファネル（シェア目標の分母に直結）

**V3.2_FORMAT.md「シェア目標の分母」で言う「対処可能市場」は、公式には SAM / SOM に対応する。**
分母を説明するときは、この3語のどれを指しているかを明示する。

| 正式用語 | 公式の定義（引用） | 出典 |
|---|---|---|
| **TAM（対応可能な全体の市場規模）** | 「TAMは total addressable market（対応可能な全体の市場規模）の略です」 | [tam-sam-som](https://advertising.amazon.com/ja-jp/library/guides/tam-sam-som) |
| **SAM（サービスを提供できる対応可能な市場規模）** | 「SAMは serviceable addressable market（サービスを提供できる対応可能な市場規模）の略です」 | [tam-sam-som](https://advertising.amazon.com/ja-jp/library/guides/tam-sam-som) |
| **SOM（サービスを提供できる獲得可能な市場規模）** | 「SOMは serviceable obtainable market（サービスを提供できる獲得可能な市場規模）の略です」 | [tam-sam-som](https://advertising.amazon.com/ja-jp/library/guides/tam-sam-som) |
| **マーケティングファネル** | 「お客様が購入までの過程でたどるコースについてわかりやすく概説しています。…カスタマージャーニーに沿ってお客様とつながり、はたらきかける上で役立つフレームワークです」 | [marketing-funnel](https://advertising.amazon.com/ja-jp/library/guides/marketing-funnel) |
| **ブランドの認知（度）** | 「消費者が特定のブランドのことをどれほどよく知っているかを指します。消費者がブランドのロゴ、名前、商品、その他のアセットをどの程度認識できるかによって測定されます」 | [brand-awareness](https://advertising.amazon.com/ja-jp/library/guides/brand-awareness) |
| **検討促進の広告** | 「ミッドファネルのマーケティング戦略で、まだ購入を決めていないものの、商品情報を収集して選択肢を比較している見込み客にアプローチすることを目的としています」 | [consideration-advertising](https://advertising.amazon.com/ja-jp/library/guides/consideration-advertising) |
| **顧客維持** | 「ブランドが一定期間において顧客を維持できることを指します」 | [customer-retention](https://advertising.amazon.com/ja-jp/library/guides/customer-retention) |
| **OKR（目標と主要な結果）** | 「計測可能な目標を定義し、その結果を追跡するために使用される目標設定方法です。このフレームワークでは、目標とは最終目標を指し、主要な結果とはその目標を達成する方法のことを指します」 | [objectives-and-key-results](https://advertising.amazon.com/ja-jp/library/guides/objectives-and-key-results) |

## 6. 商品識別と物流

| 正式用語 | 公式の定義（引用） | 出典 |
|---|---|---|
| **ASIN** | 「『ASIN 標準識別番号』の略で、AmazonストアでAmazonが商品（商品のバリエーションやバージョンを含む）に割り当てる10桁の文字と数字からなる一意」の識別番号。「同じ商品の出品情報を1つの商品詳細ページにまとめ、在庫を整理するのに役立ちます」 | [asins-introduction](https://advertising.amazon.com/ja-jp/library/guides/asins-introduction) |
| **フルフィルメント by Amazon（FBA）** | 「Amazonの出品者様が注文の出荷プロセス全体をAmazonに外注できる包括的なロジスティクスサービスです」 | [fba](https://advertising.amazon.com/ja-jp/library/guides/fba) |

## 7. 日本語の公式ページが無い用語（英語ページのみ・2026-09-09 時点）

次の3語は、`ja-jp` の URL でも**英語ページが返る**（日本語版が存在しない）。日本語表記は
**5co 側の暫定**であり、公式表記ではない。スライドでは英語略語をそのまま使い、初出で意味を添える。

| 略語 | 英語ページの定義（引用） | 5co の暫定日本語 | 出典 |
|---|---|---|---|
| **ROAS** | 「Return on Advertising Spend (ROAS) is a marketing metric that measures a specific ad campaign and how it has impacted revenue」 | 広告費用対効果 | [return-on-ad-spend-roas](https://advertising.amazon.com/ja-jp/library/guides/return-on-ad-spend-roas) |
| **CVR** | 「Conversion rate is a marketing metric that measures the number of conversions divided by the total size of your audience」 | コンバージョン率 | [conversion-rate](https://advertising.amazon.com/ja-jp/library/guides/conversion-rate) |
| **KPI** | 「A key performance indicator (KPI) is a quantifiable metric that measures the performance or progress of specific business goals and objectives」 | 重要業績評価指標 | [key-performance-indicator](https://advertising.amazon.com/ja-jp/library/guides/key-performance-indicator) |

**未確認**: **NTB（New to Brand）** と **TACoS** は、Amazon Ads の日本語ガイド一覧（272ページ・sitemap 由来）に
該当ページが見つからなかった。`TERMS_AMAZON.md` の定義は**出典未確認のまま**であり、セラーセントラル／
Amazon Ads ヘルプで裏取りしてから確定させる。

---

## 8. 5co の現行表記との差分（要判断）

`TERMS_AMAZON.md` の表記と公式表記がずれている箇所。**このファイルは公式を記録するだけで、
社内表記をどうするかはオーナー判断**（COPY_GUIDE ルール6 の趣旨では公式に寄せる）。

| 現行の 5co 表記 | Amazon Ads 公式 | 提案 |
|---|---|---|
| `ACoS` | **ACOS**（広告費売上高比率） | ACOS に統一。ACoS は業界慣用表記で誤りではないが、正典は公式に合わせる |
| 「スポンサープロダクト（SP）」 | **スポンサープロダクト広告** | 「広告」まで含めて書く。SP/SB/SD の略記は図中のみ、凡例で正式名称 |
| 「対処可能市場」（V3.2_FORMAT.md「シェア目標の分母」） | **SAM / SOM** | 分母の説明で「SAM（サービスを提供できる対応可能な市場規模）」等を併記し、造語に見えないようにする |

## 9. 出典の採取方法（再現手順）

```bash
# 日本語ガイドの全URLは sitemap から取得できる（2026-09-09 時点で 272 ページ）
for i in $(seq 1 12); do curl -sS -L "https://advertising.amazon.com/sitemap$i.xml"; done \
  | grep -o '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g' | grep '/ja-jp/library/guides/'
```

- `advertising.amazon.com/academy`（Amazon Adsアカデミー）は**受講コンテンツで、用語集ではない**。
  用語の定義は `library/guides/<slug>` にあり、こちらはサーバー側で日本語本文が返るため機械取得できる
- `getting-started/glossary` は**現在リダイレクトされ、用語集ページとして存在しない**（2026-09-09 確認）

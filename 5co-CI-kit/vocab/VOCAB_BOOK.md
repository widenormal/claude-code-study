# Amazon Ads 語彙ブック（日本語・英語・中国語）

- 版: v0.2（2026-10-30）／担当: コピーライターBot／正本: **`5co-hub/template` の `5co-CI-kit/vocab/`**（このファイル。使い方＝同じフォルダの `README.md`）
- 用途: **社内調査用**。言葉選びの基準にする。Amazon の文章は対外文章にそのまま使わない。5 co. が Amazon や公式・認定パートナーを名乗る表現はしない。
- 定義は 5 co. による短い要約（Amazon の文章の写しではない）。Amazon の正式表記は取得ページの出現頻度と `5co-CI-kit/TERMS_AMAZON_ADS.md` で確認。
- 収録: **98 概念**（うち NG語の衝突 7）。出現回数・ページ数・出典URLは `vocab_book.csv`（同じフォルダ）。DB 側の自動抽出語（カタカナ・略語 1,075 語）は `amazon_ads_content.sqlite` の `terms`（kind='auto'）。
- この版で数えたページ: ja-jp 1645／en-us 1769／zh-cn 1691（html lang がロケールと一致したページのみ）。
- 更新（生成元の収集 DB・スクリプトは git に入れない＝共用作業箱 `knowledge/copy/amazon-ads-db/` に置く）: 収集が進んだら `python3 scripts/build_vocab.py v0.x` を再実行（定義・使う/使わない語は `scripts/vocab_curated.py` を手で直す）。表記が変わった語は CHANGELOG に書く。
- 絞り込み: 全種類のページで数えた版。ページの種類ラベル（product / solution / guide / case_study / news / release_note / ad_spec / policy / legal / careers / blog / training / event / company / form_lp / home）は `csv/page_labels.csv` と DB の `page_labels` 表（`scripts/label_pages.py` で URL のパスから判定）。種類で絞るときは `python3 scripts/build_vocab.py v0.x --labels=product,solution,guide` のように実行すると `VOCAB_BOOK_product-solution-guide.md` などが別名で出る。概念ごとの種類別ページ数は CSV の `pages_by_label` 列。
- 中国語列: zh-cn（簡体字・中国本土向け）の表記。「（未取得）」はページ未収集、「（該当なし・要確認）」は収集済みページに候補語が出なかったもの。

## 1. ブランド・ツール

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| Amazon Ads | Amazon Ads | 亚马逊广告 | Amazonの広告事業・広告サービス全体の名称。 | 出典表記・サービス名を指すとき | Amazon Ads／Amazon 広告（一般名） | 「Amazon公式」「Amazon Ads パートナー」など当社が公式・提携に見える書き方 | guide・release_note・case_study |
| 広告コンソール | Advertising console | 广告平台 | 広告主が広告を作成・管理する管理画面。 | 運用の手順説明 | 広告コンソール | 管理画面（曖昧。セラー/ベンダーセントラルと区別） | release_note・guide・news |

## 2. 広告プロダクト・フォーマット

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| スポンサー広告 | sponsored ads | 推广广告 | 検索結果や商品詳細ページに出るセルフサービス型広告の総称（下の3種などを含む）。 | 広告種別をまとめて言うとき | スポンサー広告 | スポンサード広告（ド付き） | guide・case_study・release_note |
| スポンサープロダクト広告 | Sponsored Products | 商品推广 | 個々の商品を宣伝するクリック課金型の広告。 | 商品単位の広告施策 | スポンサープロダクト広告（略記SPは図中のみ） | スポンサードプロダクト／「スポンサープロダクト」で切る | guide・case_study・release_note |
| スポンサーブランド広告 | Sponsored Brands | 品牌推广 | ブランドロゴや複数商品を見出し付きで見せる広告。 | ブランド単位の露出施策 | スポンサーブランド広告 | スポンサードブランド | guide・case_study・release_note |
| スポンサーディスプレイ広告 | Sponsored Display | 展示型推广 | 閲覧・購買の傾向に合わせてAmazon内外に出すディスプレイ型のセルフサービス広告。 | リターゲティング・外部面への配信 | スポンサーディスプレイ広告 | スポンサードディスプレイ | release_note・guide・case_study |
| スポンサーTV広告 | Sponsored TV | Sponsored TV | ストリーミングTV面にセルフサービスで出せる動画広告。 | TV面への出稿の話題 | スポンサーTV広告 | — | release_note・guide・product |
| Amazon DSP | Amazon DSP | 亚马逊 DSP | Amazonのプログラマティック広告の買付ツール（製品名）。 | Amazon内外の在庫をまとめて買う話 | Amazon DSP | 「DSP」単独でAmazon製品を指す | release_note・case_study・guide |
| デマンドサイドプラットフォーム（DSP） | DSP | 需求方平台（DSP） | 広告主側が複数の取引所の広告枠を自動で買い付ける仕組みの一般名。 | アドテクの一般説明 | DSP（初出で正式名称を併記） | — | release_note・case_study・guide |
| Amazon Marketing Cloud（AMC） | AMC | 亚马逊营销云 | 広告主が安全な環境で広告と購買のデータを集計・分析できるクリーンルーム型の分析環境。 | 分析・効果検証の話題 | Amazon Marketing Cloud（AMC） | 「データベース提供」「データ連携」など当社NG語での説明 | case_study・guide・release_note |
| Amazon Marketing Stream | Amazon Marketing Stream | Amazon Marketing Stream | 広告の指標を短い間隔で配信する仕組み。 | 技術者向けの説明（当社対外文では原則触れない） | Amazon Marketing Stream（固有名として） | リアルタイム・API（当社NG語） | guide・case_study・release_note |
| ブランドストア（Amazonストア内） | Brand Store | 品牌旗舰店 | ブランドがAmazon内に持てる複数ページの専用ページ。 | ブランドページの話題 | ブランドストア | 「Amazonストア」（Amazon全体の売り場と紛れる） | guide・case_study・release_note |
| 投稿 | Posts | 帖子 | ブランドが画像投稿を商品ページ周辺に流せる機能。 | SNS的な発信の話題 | 投稿（Amazon Posts） | — | guide・policy・case_study |
| クリエイティブ | creative | 创意 | 広告の画像・動画・文言などの表現物。 | 制作の話題 | クリエイティブ | — | guide・release_note・case_study |
| 動画広告 | video ads | 视频广告 | 動画で見せる広告。 | フォーマットの話題 | 動画広告 | — | guide・case_study・release_note |
| ディスプレイ広告 | display ads | 展示广告 | 画像・アニメーション等の視覚要素で見せるWeb広告。 | フォーマットの話題 | ディスプレイ広告 | — | guide・case_study・release_note |
| ストリーミングTV広告 | Streaming TV ads | 流媒体电视广告 | ネット配信のTV番組・映画の中に出る広告。 | TV面の話題 | ストリーミングTV広告 | — | guide・case_study・news |
| 音声広告 | audio ads | 音频广告 | 音楽・ポッドキャスト等の音声配信内の広告。 | フォーマットの話題 | オーディオ広告／音声広告（1文書で統一） | — | guide・solution・product |
| 検索広告 | search ads | 搜索广告 | 検索結果に連動して出る広告の一般名。 | 一般的な検索広告 | 検索広告（一般）／Amazon内はスポンサー広告 | — | guide・case_study・release_note |

## 3. 指標

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| 広告費売上高比率（ACOS） | ACOS (advertising cost of sales) | 广告投入产出比（ACOS） | 広告費を広告経由の売上で割った比率。低いほど効率が良い。 | 広告効率の議論 | ACOS（大文字）／初出で「広告費 ÷ 広告経由売上」 | ACoS（社内正典は公式表記に寄せる）／「広告効率」だけで書く | case_study・guide・release_note |
| 総広告費売上高比率（TACOS）※用例少 | TACOS | TACOS | 広告費を総売上（広告経由以外も含む）で割った比率。 | 事業全体での広告負担の議論 | TACOS（初出で式を書く） | ACOSと混用 | case_study・guide |
| 広告費用対効果（ROAS） | ROAS | ROAS | 広告経由の売上を広告費で割った値。ACOSの逆数に近い。 | 投資回収の議論 | ROAS（広告費用対効果） | 投資対効果（ROIと紛れる） | guide・case_study・release_note |
| 費用対効果 | ROI | 投资回报率 | 投資額に対して得た利益の割合。広告に限らない一般指標。 | 経営視点の効果説明 | ROI／費用対効果 | ROASとの混用 | guide・case_study・release_note |
| クリック単価（CPC）／クリック課金 | cost-per-click | 单次点击成本（CPC） | 1クリックあたりに払う広告費。課金方式の名前としても使う。 | 入札・費用の説明 | クリック単価（CPC） | — | guide・case_study・product |
| クリックスルー率（CTR） | click-through rate | 点击率 | 表示回数のうちクリックされた割合。 | 広告の反応の比較 | クリックスルー率（CTR） | クリック率（自社サイトで要統一） | guide・case_study・release_note |
| コンバージョン率 | conversion rate | 转化率 | クリックや訪問のうち購入などの成果に至った割合。 | 商品ページの効果の説明 | コンバージョン率 | 転換率・成約率 | guide・case_study・release_note |
| コンバージョン | conversion | 转化 | 購入・登録など、狙った成果が起きること。 | 成果の定義 | コンバージョン | — | guide・case_study・release_note |
| インプレッション | impressions | 展示量 | 広告が表示された回数。 | 露出量の説明 | インプレッション（指標として）／露出（一般語） | — | guide・case_study・release_note |
| クリック | click | 点击 | 広告が押された回数。 | 反応量の説明 | クリック数 | — | guide・release_note・case_study |
| 1,000回表示あたりの単価（CPM） | CPM | 千次展示成本（CPM） | 広告を1,000回表示するのにかかる費用。 | 認知施策の費用比較 | CPM（1,000回表示あたりの単価） | — | guide・release_note・case_study |
| ブランド新規顧客 | new-to-brand | 品牌新客 | 過去一定期間にそのブランドを買っていない人による購入。 | 新規獲得の評価 | ブランド新規顧客（NTB） | 「新規」とだけ書く | case_study・guide・release_note |
| リーチ | reach | 触达 | 広告が届いた人の数・範囲。 | 認知施策の規模 | リーチ | — | guide・case_study・release_note |
| フリークエンシー | frequency | 频率 | 同じ人に広告が届いた平均回数。 | 接触回数の設計 | フリークエンシー | フリクエンシー（表記ゆれ） | guide・release_note・case_study |
| シェア・オブ・ボイス | share of voice | 展示份额 | ある市場での露出のうち自社が占める割合。 | 競合比較 | シェア・オブ・ボイス（SOV） | 棚シェア | guide・case_study・release_note |
| ビューアビリティ | viewability | 可见性 | 表示された広告のうち、実際に見られる状態だった割合。 | ディスプレイ・動画の品質評価 | ビューアビリティ | — | guide・case_study・ad_spec |
| KPI | KPIs | KPI | 目標の達成度を測るための主要な数値。 | 目標設計 | KPI | — | guide・case_study・release_note |

## 4. 測定・分析

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| Amazonアトリビューション | Amazon Attribution | Amazon Attribution | Amazon外のメディア施策がAmazon上の行動にどう効いたかを測る計測ツール。 | 外部集客の効果測定 | Amazonアトリビューション | — | guide・release_note・solution |
| インクリメンタル | incremental | 增量 | 広告がなかった場合と比べて上乗せされた効果。 | 効果検証 | 増分効果（インクリメンタリティ） | — | case_study・guide・release_note |
| ブランドリフト | Brand Lift | 品牌提升 | 広告接触で認知・好意などがどれだけ上がったかを調査で測る指標。 | 認知施策の評価 | ブランドリフト | — | guide・case_study・release_note |
| MMM | MMM | MMM | 売上への各施策の寄与を統計モデルで推定する手法。 | 予算配分の議論 | マーケティングミックスモデリング（MMM） | — | release_note・case_study・guide |
| 測定 | measurement | 衡量 | 広告の成果を数値で確かめること。 | 効果検証全般 | 測定／効果測定 | 計測と混在させない（1文書で統一） | guide・case_study・release_note |
| レポート | reporting | 报告 | 結果を集計して見られる形にすること・その出力物。 | 結果共有の説明 | レポーティング（可） | レポートサービス・定期配信（当社NG語） | guide・release_note・news |
| アトリビューション | attribution | 归因 | 成果をどの接点・施策のおかげと見るかの割り当て。 | 効果の割り振りの説明 | アトリビューション | — | guide・case_study・release_note |

## 5. ターゲティング

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| キーワードターゲティング | keyword targeting | 关键词投放 | 検索語句を指定して広告を出す方法。 | 検索広告の設計 | キーワードターゲティング | — | guide・case_study・release_note |
| 商品ターゲティング | product targeting | 商品投放 | 特定の商品・カテゴリー・ブランドを指定して広告を出す方法。 | 競合・関連商品面への配信 | 商品ターゲティング | — | guide・release_note・blog |
| オーディエンス | audiences | 受众 | 広告を届けたい人の集まり（属性・行動で定義）。 | 配信対象の説明 | オーディエンス | — | guide・case_study・release_note |
| オートターゲティング | automatic targeting | 自动投放 | Amazon側が関連する検索語・商品を自動で選んで配信する設定。 | 運用設定の説明 | オートターゲティング | 自動ターゲティング（表記ゆれ） | guide・case_study・release_note |
| マニュアルターゲティング | manual targeting | 手动投放 | キーワードや商品を広告主が自分で指定する設定。 | 運用設定の説明 | マニュアルターゲティング | 手動ターゲティング（表記ゆれ） | guide・case_study・release_note |
| 除外キーワード | negative keywords | 否定关键词 | 広告を出したくない検索語を指定する設定。 | 無駄打ちの抑制 | 除外キーワード | ネガティブキーワード | guide・case_study・blog |
| リマーケティング | remarketing | 再营销 | 過去に接触した人に再び広告を出す手法。 | 再訪促進の施策 | リマーケティング | — | case_study・guide・policy |
| フリークエンシーキャップ | frequency caps | 频次上限 | 同じ人への表示回数に上限を設ける設定。 | 接触過多の抑制 | フリークエンシーキャップ | — | guide・release_note・case_study |
| マッチタイプ | match types | 精准匹配 | 指定キーワードと検索語をどこまで厳密に合わせるかの区分（完全・フレーズ・部分）。 | 検索広告の設計 | マッチタイプ（完全一致／フレーズ一致／部分一致） | — | guide・case_study・news |

## 6. キャンペーン運用

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| 入札 | bid | 竞价 | 広告1クリック等に払ってよい上限額を示すこと。 | 費用設計 | 入札（額） | — | guide・release_note・case_study |
| 予算 | budget | 预算 | 広告に使う金額の上限。 | 費用設計 | 予算 | — | guide・case_study・release_note |
| キャンペーン | campaign | 广告活动 | 予算・期間・目的をまとめた広告の管理単位。 | 運用の単位 | キャンペーン | — | guide・release_note・case_study |
| 掲載枠 | placements | 广告位 | 広告が表示される場所。 | 露出場所の説明 | 掲載枠 | 広告枠・自然枠（自社サイトで要統一） | guide・case_study・ad_spec |
| キャンペーン管理 | campaign management | 广告活动管理 | キャンペーンを設定・監視・調整する一連の作業。 | サービス内容の説明 | 広告運用（当社表記は継続）／キャンペーン管理 | 稼働（当社NG言い換え） | guide・release_note・case_study |
| 最適化 | optimize | 优化 | 成果が良くなるよう設定や表現を調整すること。 | 運用の説明 | 最適化 | — | guide・release_note・case_study |
| 動的な入札 - アップとダウン（設定名） | dynamic bids | 动态竞价 | 成果の見込みに応じて入札額を自動で上下させる入札戦略。 | 運用設定の説明 | 動的な入札（設定名どおり） | 自動入札と略す | guide・case_study・blog |

## 7. アドテク

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| SSP | SSPs | SSP | 媒体側が広告枠を売るための仕組み。DSPの対。 | アドテクの説明 | SSP（初出で正式名称） | — | guide・news・release_note |
| リアルタイム入札 | RTB | 实时竞价 | 広告枠を1回の表示ごとに即時の競りで売買する方式。 | アドテクの説明（当社文は固有名として引用時のみ） | RTB（固有の方式名として） | 「リアルタイム」単独の使用（当社NG語） | guide・release_note・blog |
| 広告在庫 | ad inventory | 广告库存 | 買える広告枠の在庫。 | 媒体の説明 | 広告在庫（広告インベントリ） | — | guide・release_note・news |

## 8. 売り場・商品

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| オーガニック | organic | 自然搜索 | 広告ではない通常の検索結果・表示。 | 広告と非広告の対比 | オーガニック（検索結果） | 自然枠 | guide・case_study・blog |
| 検索結果 | search results | 搜索结果 | 検索したときに並ぶ一覧。 | 露出場所の説明 | 検索結果 | — | guide・release_note・case_study |
| 商品詳細ページ | detail page | 商品详情页 | 個別商品の説明・価格・購入ボタンがあるページ。 | 商品ページの話題 | 商品詳細ページ | 商品ページ（自社サイトで要統一） | guide・case_study・release_note |
| カテゴリー | category | 品类 | Amazonの商品分類。 | 市場・商品の区分 | カテゴリー | カテゴリ（長音なし）・棚 | guide・case_study・release_note |
| ASIN | ASIN | ASIN | Amazonが商品ごとに振る10桁の識別番号。 | 商品単位の説明 | ASIN（親/子を明示） | 商品ページ・枚・本で数える | guide・release_note・ad_spec |
| FBA | FBA | 亚马逊物流 | 出品者が保管・出荷・返品対応をAmazonに任せるサービス。 | 物流の話題 | FBA（フルフィルメント by Amazon） | — | guide・case_study・release_note |

## 9. 事業者・関係者

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| 広告主様 | advertisers | 广告主 | 広告を出す事業者。 | 対象顧客の呼称 | 広告主（敬称「様」の要否は要確認） | — | release_note・guide・news |
| 出品者 | sellers | 卖家 | Amazonで自ら販売する事業者（セラーセントラル利用）。 | 取引形態の区別 | 出品者（セラー） | ベンダーと混用 | release_note・guide・case_study |
| ベンダー | vendors | 供应商 | Amazonに商品を卸す事業者（ベンダーセントラル利用）。 | 取引形態の区別 | ベンダー | 出品者と混用 | release_note・guide・product |
| ブランド登録 | Brand Registry | 亚马逊品牌注册 | ブランドの権利者として登録する仕組み。一部広告の利用条件。 | 利用条件の説明 | ブランド登録（Amazonブランド登録） | — | guide・release_note・product |
| 代理店 | Agency | 代理商 | 広告主に代わって広告を企画・運用する会社。 | 業界構造の説明 | 代理店 | 当社を「Amazon認定代理店」等と書く | guide・case_study・release_note |
| パートナー | partner | 合作伙伴 | Amazon Adsと協業する外部企業の総称（Amazonのプログラム名でもある）。 | 業界構造の説明 | （当社の文脈では）支援会社・伴走 | 当社を「Amazon（Ads）パートナー」と書く | case_study・guide・news |
| 認定パートナー | advanced partner | 高级合作伙伴 | Amazon Adsが条件を満たした企業に与える認定区分。 | （社内調査のみ） | — | 当社が認定を受けているかのような表現すべて | case_study・guide・release_note |
| お客様 | customers | 顾客 | 商品を買う人。 | 買い手の呼称 | お客様／消費者（文脈で） | — | guide・case_study・release_note |

## 10. マーケティング概念

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| リテールメディア | retail media | 零售媒体 | 小売事業者が自社の売り場・データを使って売る広告媒体。 | 市場の説明 | リテールメディア | — | guide・case_study・news |
| フルファネル | funnel | 漏斗 | 認知から購入・再購入までの段階すべてを通して考えること。 | 施策全体の設計 | フルファネル | — | guide・case_study・news |
| 認知度 | awareness | 知名度 | ブランドや商品がどれだけ知られているか。 | 上位ファネルの目的 | 認知（度） | — | guide・case_study・release_note |
| 検討 | consideration | 考虑 | 購入候補として比べている段階。 | 中位ファネルの目的 | 検討 | 併願（当社NG造語） | guide・case_study・release_note |
| ロイヤルティ | loyalty | 忠诚度 | 同じブランドを繰り返し選ぶ度合い。 | 既存顧客の施策 | ロイヤルティ | ロイヤリティ（表記ゆれ） | guide・case_study・solution |
| カスタマージャーニー | customer journey | 消费者旅程 | 購入までにたどる流れ全体。 | 施策設計の説明 | カスタマージャーニー／購入経路 | 導線・動線（自社サイトで要統一） | guide・case_study・news |
| タッチポイント | touchpoints | 触点 | 顧客がブランドと接する場面。 | 施策設計の説明 | タッチポイント | 顧客接点（統一するなら） | guide・case_study・news |
| ショッピングシグナル | first-party signals | 第一方信号 | Amazon上の閲覧・購買などの行動から得られる手がかり。 | Amazonのデータを指すとき | ショッピングシグナル（Amazon側を指すとき） | 当社データとの混同／データ提供・データ販売（当社NG語） | guide・news・release_note |
| インサイト | insights | 洞察 | データから読み取った示唆。 | 分析結果の表現 | インサイト | — | guide・case_study・release_note |
| プログラマティック | programmatic | 程序化 | 広告枠の売買をシステムで自動化すること。 | アドテクの説明 | プログラマティック | — | guide・release_note・news |
| アドテクノロジー | ad tech | 广告技术 | 広告の配信・売買・計測を支える技術の総称。 | 業界の説明 | アドテクノロジー | — | guide・news・careers |
| EC | eCommerce | 电子商务 | インターネット上での商品販売。 | 市場の説明 | eコマース（小文字e） | Eコマース | case_study・guide・release_note |
| 売上 | sales | 销售 | 売れた金額（または数量）。 | 成果の説明 | 売上 | 売り上げ（1文書で統一） | guide・case_study・release_note |
| TAM／SAM／SOM | TAM / SAM / SOM | TAM／SAM／SOM | 市場規模の3段階（全体・提供可能・獲得可能）。 | シェア目標の分母の説明 | TAM／SAM／SOM（初出で意味を併記） | 対処可能市場（造語に見える） | guide・blog・case_study |
| 顧客維持 | retention | 留存 | 既存の顧客が離れずに買い続けること。 | 既存顧客施策 | 顧客維持 | — | guide・case_study・release_note |

## 11. Amazonは使うが当社は使わない語（NG語の衝突）

| 日本語（Amazon表記） | English | 中文（zh-cn） | 定義（要約） | 使う場面 | 当社で使う | 当社で使わない | 主な出現ページの種類 |
|---|---|---|---|---|---|---|---|
| ダッシュボード | dashboard | 控制面板 | （Amazonは使う語）指標を一画面にまとめた画面。 | 社内調査のみ | 状況を一覧で把握／定点で確認 | ダッシュボード（当社NG語） | guide・release_note・case_study |
| リアルタイム | real-time | 实时 | （Amazonは使う語）即時であること。 | 社内調査のみ | 速やかに／タイムリーに | リアルタイム（当社NG語） | guide・case_study・release_note |
| API | API | API | （Amazonは使う語）システム同士の接続口。 | 社内調査のみ | 仕組み／ツール | API・システム連携（当社NG語） | release_note・guide・policy |
| ダウンロード | Download | 下载 | （Amazonは使う語）資料・データの取得。 | 社内調査のみ | 資料のご請求 | ダウンロード（当社NG語） | ad_spec・guide・release_note |
| CSV | CSV | CSV | （Amazonは使う語）表形式のファイル形式。 | 社内調査のみ | — | CSV（当社NG語） | release_note・guide |
| 毎日 | daily | 每日 | （Amazonは使う語）毎日・日単位。 | 社内調査のみ | 毎営業日／こまめに | 日次（当社NG語） | guide・case_study・release_note |
| データ統合 | Data integration | 数据整合 | （Amazonは使う語）データをつなぐこと。 | 社内調査のみ | — | データ連携（当社NG語） | guide・case_study・news |

## 注記

- 「当社で使う／使わない」は `knowledge/copy/GLOSSARY.md`・`5co-CI-kit/TERMS_AMAZON.md`／`TERMS_AMAZON_ADS.md`・DB の `mismatches` 表に基づく。確定していない統一（クリック率→クリックスルー率 等）は自社サイト修正の提案段階。
- English 列は en-us の出現上位の綴り（小文字化して集計）。固有名は大文字で書く（Sponsored Products 等）。
- 中国語の候補語は 5 co. が用意した正規表現で数えた結果。候補に無い表記は拾えないため、0件の語は zh-cn ページを開いて確認する。

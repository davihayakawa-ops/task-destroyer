"""Configuration for per-item generation screens."""

IP_ITEMS = [  # (key, ja_label, pt_label)
    ("main_visual", "🖼️ 商品ページ メインビジュアル", "🖼️ Visual Principal da Página"),
    ("product_only", "📦 商品単体画像", "📦 Imagem do Produto"),
    ("usage_scene", "🌿 使用シーン画像", "🌿 Cena de Uso"),
    ("benefit", "✨ ベネフィット訴求画像", "✨ Imagem de Benefício"),
    ("comparison", "⚖️ 比較画像", "⚖️ Imagem de Comparação"),
    ("ad_banner", "📢 広告バナー画像", "📢 Banner Publicitário"),
    ("sns_post", "📱 SNS投稿画像", "📱 Imagem para SNS"),
    ("story", "📖 ストーリー用画像", "📖 Imagem para Stories"),
]

IP_PRESETS = [  # (key, ja_name, pt_name, item_keys)
    ("shopify", "🛒 Shopifyページ制作セット", "🛒 Set Shopify",
     ["main_visual", "product_only", "usage_scene", "benefit"]),
    ("sns", "📱 SNS素材セット", "📱 Set SNS",
     ["sns_post", "story", "usage_scene"]),
    ("ads", "📢 広告運用セット", "📢 Set Anúncios",
     ["ad_banner", "comparison", "benefit"]),
    ("full", "⚡ フル生成", "⚡ Geração Completa",
     [k for k, _, _ in IP_ITEMS]),
    ("custom", "✏️ カスタム", "✏️ Personalizado", []),
]

VS_ITEMS = [
    ("script_15s", "⏱️ 15秒動画台本", "⏱️ Vídeo 15s"),
    ("script_30s", "⏱️ 30秒動画台本", "⏱️ Vídeo 30s"),
    ("script_45s", "⏱️ 45秒動画台本", "⏱️ Vídeo 45s"),
    ("script_60s", "⏱️ 60秒動画台本", "⏱️ Vídeo 60s"),
    ("tiktok", "🎵 TikTok用台本", "🎵 TikTok"),
    ("reels", "📸 Instagram Reels用台本", "📸 Instagram Reels"),
    ("yt_shorts", "▶️ YouTube Shorts用台本", "▶️ YouTube Shorts"),
    ("narration", "🎤 読み上げ用ナレーション", "🎤 Narração"),
    ("timeline", "📋 秒数別構成", "📋 Cronograma"),
    ("telop", "💬 テロップ版", "💬 Versão Legendada"),
    ("shooting", "🎬 撮影指示付き台本", "🎬 Com Direção de Filmagem"),
]

VS_PRESETS = [
    ("sns", "📱 SNS投稿セット", "📱 Set SNS",
     ["script_15s", "script_30s", "tiktok", "reels"]),
    ("ads", "📢 広告運用セット", "📢 Set Anúncios",
     ["script_30s", "script_60s", "shooting", "timeline"]),
    ("full", "⚡ フル生成", "⚡ Geração Completa",
     [k for k, _, _ in VS_ITEMS]),
    ("custom", "✏️ カスタム", "✏️ Personalizado", []),
]

VS_DURATIONS = [
    ("15s", "15秒", "15s"),
    ("30s", "30秒", "30s"),
    ("45s", "45秒", "45s"),
    ("60s", "60秒", "60s"),
]

VS_TYPES = [
    ("tiktok", "🎵 TikTok用台本", "🎵 TikTok"),
    ("reels", "📸 Instagram Reels用台本", "📸 Instagram Reels"),
    ("yt_shorts", "▶️ YouTube Shorts用台本", "▶️ YouTube Shorts"),
    ("ad_script", "📢 広告用台本", "📢 Roteiro de Anúncio"),
    ("narration", "🎤 読み上げナレーション", "🎤 Narração"),
    ("timeline", "📋 秒数別構成", "📋 Cronograma"),
    ("shooting", "🎬 撮影指示付き台本", "🎬 Direção de Filmagem"),
    ("higgs_marketing_studio", "🧪 Higgs Marketing Studio用プロンプト", "🧪 Prompt Higgs Marketing Studio"),
]

VS_COMBO_PRESETS = [
    ("sns", "📱 SNS投稿セット", "📱 Set SNS",
     ["15s", "30s"], ["tiktok", "reels", "narration"]),
    ("ads", "📢 広告運用セット", "📢 Set Anúncios",
     ["30s", "45s"], ["ad_script", "timeline", "shooting", "higgs_marketing_studio"]),
    ("shorts", "▶️ Shorts制作セット", "▶️ Set Shorts",
     ["30s", "60s"], ["yt_shorts", "timeline", "higgs_marketing_studio"]),
    ("full", "⚡ フル生成", "⚡ Geração Completa",
     [k for k, _, _ in VS_DURATIONS], [k for k, _, _ in VS_TYPES]),
    ("custom", "✏️ カスタム", "✏️ Personalizado", [], []),
]

AS_MEDIA = [  # (key, label)
    ("instagram", "Instagram"),
    ("tiktok", "TikTok"),
    ("yt_shorts", "YouTube Shorts"),
    ("facebook", "Facebook"),
    ("x", "X (Twitter)"),
    ("line", "LINE"),
    ("shopify_ad", "Shopify広告文"),
    ("google_ad", "Google広告"),
]

AS_TYPES = [  # (key, ja_label, pt_label)
    ("post", "投稿文", "Postagem"),
    ("ad_copy", "広告コピー", "Copy Publicitário"),
    ("caption", "キャプション", "Legenda"),
    ("hashtag", "ハッシュタグ", "Hashtags"),
    ("cta", "CTA", "CTA"),
    ("hook", "短いフック", "Gancho Curto"),
    ("comment_bait", "コメント誘導文", "Indutor de Comentários"),
]

AS_PRESETS = [  # (key, ja_name, pt_name, [(media,type),...])
    ("sns", "📱 SNS投稿セット", "📱 Set SNS",
     [("instagram", "post"), ("tiktok", "post"), ("instagram", "hashtag"),
      ("tiktok", "hashtag"), ("instagram", "cta"), ("tiktok", "cta")]),
    ("ads", "📢 広告運用セット", "📢 Set Anúncios",
     [("instagram", "ad_copy"), ("tiktok", "ad_copy"), ("instagram", "cta"),
      ("google_ad", "ad_copy"), ("facebook", "ad_copy")]),
    ("custom", "✏️ カスタム", "✏️ Personalizado", []),
]

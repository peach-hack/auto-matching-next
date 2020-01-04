WITH title_freqs AS (
  SELECT
    title as title_f,
    COUNT(title) as title_count
  FROM posts
  GROUP BY
    title_f
),
profile_freqs AS (
  SELECT
    CONCAT(name, '_', age, '_', city) as profile,
    COUNT(CONCAT(name, '_', age, '_', city)) as profile_count
  FROM posts
  GROUP BY
    profile
)
SELECT
  posted_at,
  title,
  name,
  age,
  site,
  genre,
  prefecture,
  city,
  title_count,
  profile_count,
  created_at,
  updated_at,
  url
FROM posts as p
LEFT JOIN title_freqs ON title_f = p.title
LEFT JOIN profile_freqs ON profile = CONCAT(name, '_', age, '_', city)
WHERE
  -- タイトルが長すぎる投稿は除外
  LENGTH(p.title) < 64 --
  --
  -- 名前が長すぎる投稿は除外
  AND LENGTH(name) < 20 --
  --
  -- 地域による除外は保留。
  -- 地方から都会に来て募集してる場合がある。
  --
  -- 年齢が対象外の人は除外
  AND NOT EXISTS(
    SELECT
      age
    FROM ng_ages
    WHERE
      p.age LIKE CONCAT(age, '%')
  ) --
  --
  -- 名前にNGワードが含まれている投稿を除外
  AND NOT EXISTS(
    SELECT
      name
    FROM ng_names
    WHERE
      p.name LIKE CONCAT('%', name, '%')
  ) --
  --
  -- タイトルにNGワードが含まれている投稿を除外
  AND NOT EXISTS(
    SELECT
      word
    FROM ng_words as ng
    WHERE
      p.title LIKE CONCAT('%', word, '%')
  ) --
  --
  -- タイトルとプロフィールの出現回数がともに３回以内の投稿
  AND (
    profile_count <= 3
    AND title_count <= 3
  ) --
  -- created_atとposted_atの乖離が1日以上は除外
  AND DATEDIFF(posted_at, created_at) < 2
ORDER BY
  posted_at DESC;
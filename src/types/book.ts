export type ReadingStatus =
  | "tsundoku"
  | "reading"
  | "finished"
  | "wishlist";

export const GENRE_OPTIONS = [
  "文学・評論",
  "人文・思想",
  "社会・政治・法律",
  "ノンフィクション",
  "歴史・地理",
  "ビジネス・経済",
  "投資・金融・会社経営",
  "科学・テクノロジー",
  "医学・薬学・看護学・歯科学",
  "コンピュータ・IT",
  "アート・建築・デザイン",
  "趣味・実用",
  "スポーツ・アウトドア",
  "資格・検定・就職",
  "暮らし・健康・子育て",
  "旅行ガイド・マップ",
  "語学・辞事典・年鑑",
  "英語学習",
  "教育・学参・受験",
  "絵本・児童書",
  "コミック",
  "ライトノベル",
  "ボーイズラブ",
  "タレント写真集",
  "ゲーム攻略本",
  "エンターテイメント",
  "新書・文庫・ノベルス",
  "雑誌",
  "楽譜・スコア・音楽書",
  "カレンダー・手帳",
  "ポスター",
  "古本",
  "古書・希少本",
] as const;

export interface Book {
  id: string;
  title: string;
  author: string;
  genre: string;
  publishedDate: string;
  status: ReadingStatus;
  pageCount: number;
  rating: number;
  memo: string;
  description: string;
  thumbnail: string | null;
  purchaseUrl: string;
  finishedDate: string | null;
  createdAt: string;
  updatedAt: string;
}

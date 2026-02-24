"use client";

interface StarRatingProps {
  rating: number;
  onChange?: (rating: number) => void;
  readonly?: boolean;
  size?: "sm" | "md";
}

export default function StarRating({
  rating,
  onChange,
  readonly = false,
  size = "md",
}: StarRatingProps) {
  const sizeClass = size === "sm" ? "text-lg" : "text-2xl";

  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => {
        const starContent = star <= rating ? (
          <span className="text-yellow-400">&#9733;</span>
        ) : (
          <span className="text-gray-300">&#9734;</span>
        );

        if (readonly) {
          return (
            <span
              key={star}
              className={`${sizeClass} cursor-default transition-transform`}
            >
              {starContent}
            </span>
          );
        }

        return (
          <button
            key={star}
            type="button"
            onClick={() => onChange?.(star === rating ? 0 : star)}
            className={`${sizeClass} cursor-pointer hover:scale-110 transition-transform`}
          >
            {starContent}
          </button>
        );
      })}
    </div>
  );
}

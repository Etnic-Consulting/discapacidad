import DOMPurify from 'dompurify';

const SAFE_TAGS = ['strong', 'em', 'b', 'i', 'u', 'br', 'span', 'a'];
const SAFE_ATTRS = ['href', 'title', 'target', 'rel'];

export default function SectionHead({ num, title, intro, meta }) {
  const safeIntro = intro
    ? DOMPurify.sanitize(intro, { ALLOWED_TAGS: SAFE_TAGS, ALLOWED_ATTR: SAFE_ATTRS })
    : null;
  return (
    <div className="sec">
      <div className="sec-head">
        {num && <span className="sec-num">§ {num}</span>}
        <span className="sec-title">{title}</span>
        {meta && <span className="sec-meta">{meta}</span>}
      </div>
      {safeIntro && (
        <p
          className="sec-intro"
          dangerouslySetInnerHTML={{ __html: safeIntro }}
        />
      )}
    </div>
  );
}

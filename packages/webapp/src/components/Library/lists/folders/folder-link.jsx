import { forwardRef } from 'react';
import {
  Link,
  useLocation,
} from 'react-router-dom';

// A link to the folder `data.dir` in the folder view the current page belongs to.
const FolderLink = forwardRef((props, ref) => {
  const { pathname, search: urlSearch } = useLocation();
  const { data, ...linkProps } = props;
  const parts = pathname.split('/');
  const folders = parts.indexOf('folders');
  const base = folders >= 0 ? parts.slice(0, folders + 1).join('/') : '/library/music/folders';
  const location = `${base}/${encodeURIComponent(data?.dir)}${urlSearch}`;

  return <Link ref={ref} to={location} {...linkProps} />
});
FolderLink.displayName = 'FolderLink';

export default FolderLink;

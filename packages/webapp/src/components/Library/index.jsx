import {
  Navigate,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom';

import LibraryLists from './lists';
import { activeTabAndView } from './library-header';

const storedView = () => {
  try {
    const view = localStorage.getItem('libraryLastListView');
    return view && activeTabAndView(`/library/${view}`)[0] ? view : null;
  }
  catch {
    return null;
  }
};

const Library = () => {
  const { search: urlSearch } = useLocation();
  const isSelecting = new URLSearchParams(urlSearch).get('isSelecting');
  const view = isSelecting ? 'music/albums' : (storedView() || 'continue');

  return (
    <Routes>
      <Route index element={<Navigate to={`${view}${urlSearch}`} replace />} />
      <Route path="*" element={<LibraryLists />} />
    </Routes>
  );
};

export default Library;

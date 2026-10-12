import request from './request';
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from 'vitest';

const jsonResponse = (body, options = {}) => ({
  ok: options.ok ?? true,
  status: options.status ?? 200,
  json: vi.fn().mockResolvedValue(body),
  text: vi.fn().mockResolvedValue(JSON.stringify(body)),
});

describe('request', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    delete global.fetch;
  });

  test('sends GET kwargs as query parameters', async () => {
    global.fetch.mockResolvedValue(jsonResponse([{ album: 'Mezzanine' }]));

    const response = await request('libraryItems', {
      content_types: ['album', 'playlist'],
      provider: 'local',
      query: undefined,
    });

    expect(response).toEqual({ result: [{ album: 'Mezzanine' }] });
    expect(global.fetch.mock.calls[0][0]).toBe(
      '/api/v1/library/items?content_types=album&content_types=playlist&provider=local',
    );
    expect(global.fetch.mock.calls[0][1].method).toBe('GET');
  });

  test('sends non-GET kwargs as JSON body and maps 204 to null', async () => {
    global.fetch.mockResolvedValue({ ok: true, status: 204 });

    const response = await request('play_folder', { folder: 'Music/Rock' });

    expect(response).toEqual({ result: null });
    const [path, options] = global.fetch.mock.calls[0];
    expect(path).toBe('/api/v1/player/folder');
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({ folder: 'Music/Rock' });
  });

  test('fills path parameters from kwargs', async () => {
    global.fetch.mockResolvedValue({ ok: true, status: 204 });

    await request('deleteCard', { card_id: 'a/b' });

    const [path, options] = global.fetch.mock.calls[0];
    expect(path).toBe('/api/v1/cards/a%2Fb');
    expect(options.method).toBe('DELETE');
    expect(JSON.parse(options.body)).toEqual({});
  });

  test('returns HTTP errors and unknown commands as errors', async () => {
    global.fetch.mockResolvedValue(jsonResponse({ detail: 'nope' }, { ok: false, status: 501 }));

    const { error } = await request('play');
    expect(error.message).toContain('HTTP 501');

    const { error: unknown } = await request('doesNotExist');
    expect(unknown.message).toContain('does not exist');
  });

  test('aborts requests after 15 seconds', async () => {
    vi.useFakeTimers();
    global.fetch.mockImplementation((_, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => {
        const error = new Error('aborted');
        error.name = 'AbortError';
        reject(error);
      });
    }));

    const pending = request('playerstatus');
    await vi.advanceTimersByTimeAsync(15000);

    const { error } = await pending;
    expect(error.message).toBe('Request timed out');
  });
});

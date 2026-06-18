import { jest, describe, it, expect } from '@jest/globals';
import { corsConfig } from '../../src/middleware/corsConfig';

jest.mock('../../src/config/configService', () => ({
  config: {
    ALLOWED_ORIGINS: 'http://example.com,http://another.com',
  },
  default: {
    ALLOWED_ORIGINS: 'http://example.com,http://another.com',
  }
}));

describe('corsConfig middleware', () => {
  it('should register cors middleware on the app', () => {
    const mockApp = {
      use: jest.fn(),
    };

    corsConfig(mockApp);

    expect(mockApp.use).toHaveBeenCalled();
  });
});

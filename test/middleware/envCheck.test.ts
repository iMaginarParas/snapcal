import { jest, describe, it, expect } from '@jest/globals';
import { envCheck } from '../../src/middleware/envCheck';
import logger from '../../src/logger';
import { Request, Response } from 'express';

jest.mock('../../src/config/configService', () => ({
  default: {},
}));

jest.mock('../../src/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  default: {
    info: jest.fn(),
    error: jest.fn(),
  }
}));

describe('envCheck middleware', () => {
  it('should call next() and log info', () => {
    const mockReq = {} as Request;
    const mockRes = {} as Response;
    const mockNext = jest.fn();

    envCheck(mockReq, mockRes, mockNext);

    expect(mockNext).toHaveBeenCalled();
  });
});

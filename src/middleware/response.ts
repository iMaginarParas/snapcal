import { Response } from 'express';

export function sendSuccess(res: Response, data: any, statusCode: number = 200) {
  return res.status(statusCode).json({
    success: true,
    data
  });
}

export function sendError(res: Response, errorMsg: string, statusCode: number = 500) {
  return res.status(statusCode).json({
    success: false,
    error: errorMsg
  });
}

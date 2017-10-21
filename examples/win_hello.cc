#include <windows.h>
#include <stdlib.h>
#include <string.h>
#include <tchar.h>
#include <iostream>
#include <cstdint>

using namespace std;

static TCHAR szWindowClass[] = _T("win32app");
static TCHAR szTitle[] = _T("Win32 Guided Tour Application");

HINSTANCE hInst;

// Forward declarations of functions included in this code module:
LRESULT CALLBACK WndProc(HWND, UINT, WPARAM, LPARAM);

int CALLBACK WinMain(
  _In_ HINSTANCE hInstance,
  _In_ HINSTANCE hPrevInstance,
  _In_ LPSTR     lpCmdLine,
  _In_ int       nCmdShow
) {
  #ifdef DEBUG
    if (AllocConsole()) {
      FILE *fp_out;
      FILE *fp_in;
      freopen_s(&fp_out, "CONOUT$", "w", stdout);
      freopen_s(&fp_in, "CONIN$", "rt", stdin);
      SetConsoleTitle("Debug Console");
    }

    printf("Hello Windows\n");
  #endif

  // Redirect the CRT standard input, output, and error handles to the console
  // create the console
  WNDCLASSEX wcex;
  wcex.cbSize = sizeof(WNDCLASSEX);
  wcex.style          = CS_HREDRAW | CS_VREDRAW;
  wcex.lpfnWndProc    = WndProc;
  wcex.cbClsExtra     = 0;
  wcex.cbWndExtra     = 0;
  wcex.hInstance      = hInstance;
  wcex.hCursor        = LoadCursor(NULL, IDC_ARROW);
  wcex.hbrBackground  = (HBRUSH)(COLOR_WINDOW+1);
  wcex.lpszMenuName   = NULL;
  wcex.lpszClassName  = szWindowClass;

  if (!RegisterClassEx(&wcex)) {
    MessageBox(0, _T("Call to RegisterClassEx failed!"), _T("Win32 Guided Tour"), 0);
    return 1;
  }

  hInst = hInstance;

  HWND hWnd = CreateWindow(
    szWindowClass,
    szTitle,
    WS_OVERLAPPEDWINDOW,
    CW_USEDEFAULT, CW_USEDEFAULT,
    500, 100,
    NULL,
    NULL,
    hInstance,
    NULL
  );

  if (!hWnd) {
    MessageBox(
      0,
      _T("Call to CreateWindow failed!"),
      _T("Win32 Guided Tour"),
      0
    );

    return 1;
  }

  // The parameters to ShowWindow explained:
  // hWnd: the value returned from CreateWindow
  // nCmdShow: the fourth parameter from WinMain
  ShowWindow(hWnd, nCmdShow);
  UpdateWindow(hWnd);

  // Main message loop:
  MSG msg;
  while (GetMessage(&msg, NULL, 0, 0)) {
    TranslateMessage(&msg);
    DispatchMessage(&msg);
  }

  return (int) msg.wParam;
}

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
  PAINTSTRUCT ps;
  HDC hdc;
  TCHAR greeting[] = _T("Hello, World!");

  switch (message) {
  case WM_PAINT:
    hdc = BeginPaint(hWnd, &ps);

    TextOut(
      hdc,
      5,
      5,
      greeting,
      _tcslen(greeting)
    );

    EndPaint(hWnd, &ps);
    break;
  case WM_DESTROY:
    PostQuitMessage(0);
    break;
  default:
    return DefWindowProc(hWnd, message, wParam, lParam);
    break;
  }

  return 0;
}

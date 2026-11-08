#pragma once

// Xcode 26 no longer implicitly declares the ARM yield intrinsic used by Qt's
// qyieldcpu.h. This file is force-included before the generated SIP headers.
// The rcc extension is universal, so include the ARM header only for its arm64
// compilation slice.
#if defined(__APPLE__) && defined(__arm64__)
#include <arm_acle.h>
#endif
